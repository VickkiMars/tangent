import asyncio
import json
import time
import inspect
from typing import List, Dict, Any, Callable, Optional
import structlog
import litellm

# Assuming schemas are defined in a separate file named schemas.py
from schemas import (
    SubTask,
    AgentBlueprint,
    SynthesisManifest,
    A2AMessage,
    MessagePayload
)
from blackboard import EventBlackboard
from registry import GlobalToolRegistry
from telemetry import get_tracer
from llm_provider import LLMFactory

logger = structlog.get_logger(__name__)
tracer = get_tracer(__name__)

class JITCompiler:
    def __init__(self, blackboard: EventBlackboard, registry: GlobalToolRegistry):
        self.blackboard = blackboard
        self.registry = registry
        self.listener_task = None
        self.agent_tasks: set = set()
        self.hibernated_task_ids: set = set()
        self._user_id: str = "dev_user"
        self._tenant_id: str = "tenant_1"

    @staticmethod
    def _normalize_message(msg) -> dict:
        """Convert a LiteLLM response message to a plain dict, stripping provider-specific fields
        from tool_calls to avoid Pydantic serialization warnings on the next LLM call."""
        d = {"role": msg.role, "content": msg.content}
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            d["tool_calls"] = [
                {
                    "id": (tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "")) or "",
                    "type": "function",
                    "function": {
                        "name": (tc.get("function", {}).get("name") if isinstance(tc, dict)
                                 else getattr(getattr(tc, "function", None), "name", "")) or "",
                        "arguments": (tc.get("function", {}).get("arguments") if isinstance(tc, dict)
                                      else getattr(getattr(tc, "function", None), "arguments", "{}")) or "{}"
                    }
                }
                for tc in tool_calls
            ]
        return d

    async def unblock_agent(self, task_id: str, human_input: str):
        """Publishes a message to the blackboard to unblock a hibernated agent."""
        unblock_msg = A2AMessage(
            message_id=f"unblock_{task_id}_{int(time.time())}",
            thread_id=task_id,
            sender_id="human",
            receiver_id="unblock_agent",
            performative="inform",
            payload=MessagePayload(natural_language=human_input),
            timestamp=time.time()
        )
        await self.blackboard.publish(unblock_msg)

    async def start_resume_listener(self, manifest: SynthesisManifest, tasks: List[SubTask]):
        """Polls for unblocking events to respawn hibernated agents."""
        queue = self.blackboard.subscribe("unblock_agent")
        task_lookup = {t.task_id: t for t in tasks}
        blueprint_lookup = {b.target_task_id: b for b in manifest.blueprints}

        try:
            while True:
                message: A2AMessage = await queue.get()
                if message.thread_id in blueprint_lookup:
                    target_task = task_lookup[message.thread_id]
                    blueprint = blueprint_lookup[message.thread_id]
                    
                    # 1. Fetch persistent state
                    agent_state = await self.blackboard.get_agent_state(message.thread_id)
                    
                    initial_context = None
                    if agent_state:
                        initial_context = {
                            "conversation_history": agent_state.get("conversation_history", []),
                            "collected_context": agent_state.get("collected_context", {}),
                            "human_input_response": message.payload.natural_language
                        }
                    
                    logger.info("resuming_hibernated_agent", task_id=message.thread_id, has_state=bool(initial_context))

                    # 2. Respawn agent, injecting the restored context.
                    # Track the new task so execute_manifest keeps waiting for it.
                    self.hibernated_task_ids.discard(message.thread_id)
                    new_task = asyncio.create_task(self._spawn_ephemeral_agent(blueprint, target_task, initial_context=initial_context))
                    self.agent_tasks.add(new_task)
        except asyncio.CancelledError:
            self.blackboard.unsubscribe("unblock_agent", queue)

    async def execute_manifest(self, manifest: SynthesisManifest, tasks: List[SubTask], user_id: str = "dev_user", tenant_id: str = "tenant_1"):
        """Compiles and launches all agents concurrently."""
        self.manifest = manifest
        self.tasks = tasks
        self.task_lookup = {task.task_id: task for task in tasks}
        self.agent_tasks = set()
        self.hibernated_task_ids = set()
        self._user_id = user_id
        self._tenant_id = tenant_id

        self.listener_task = asyncio.create_task(self.start_resume_listener(manifest, tasks))

        for blueprint in manifest.blueprints:
            target_task = self.task_lookup[blueprint.target_task_id]
            if getattr(blueprint, "agent_type", "ephemeral") == "daemon":
                agent_thread = asyncio.create_task(self._spawn_daemon_agent(blueprint, target_task))
            else:
                agent_thread = asyncio.create_task(self._spawn_ephemeral_agent(blueprint, target_task))
            self.agent_tasks.add(agent_thread)

        # Keep running as long as active agents OR hibernated agents exist.
        # Hibernated agents live in Redis until a human unblocks them; the resume
        # listener will re-add their tasks to self.agent_tasks when that happens.
        while self.agent_tasks or self.hibernated_task_ids:
            if not self.agent_tasks:
                # All current tasks done; waiting for human to unblock hibernated agents.
                await asyncio.sleep(0.1)
                continue
            # Take a snapshot so newly-added tasks (from resume listener) are not lost.
            tasks_snapshot = set(self.agent_tasks)
            done, _ = await asyncio.wait(tasks_snapshot, return_when=asyncio.FIRST_COMPLETED)
            # Remove only the finished tasks; preserve any tasks added during the wait.
            self.agent_tasks -= done

        # Cancel the resume listener now that all agents have finished
        if self.listener_task and not self.listener_task.done():
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass

    async def _spawn_daemon_agent(self, blueprint: AgentBlueprint, task: SubTask):
        """Lifecycle of a Daemon Agent (Continuous Event Loop with Supervisor)."""
        agent_id = blueprint.agent_id
        
        while True:
            with tracer.start_as_current_span(f"daemon_lifecycle_{blueprint.agent_id}") as span:
                logger.info("daemon_spawned", agent_id=agent_id, task_id=task.task_id)
                
                # Daemons listen to their dependencies as topics
                topics = task.dependencies if task.dependencies else ["blackboard"]
                queues = [self.blackboard.subscribe(topic) for topic in topics]
                
                bound_tools = self.registry.get_ephemeral_toolkit(blueprint.injected_tools)
                llm_tool_schemas = self.registry.get_ephemeral_schemas(blueprint.injected_tools)
                
                messages = [
                    {"role": "system", "content": blueprint.persona_prompt},
                    {"role": "user", "content": f"Daemon started. Objective: {task.description}"}
                ]
                
                try:
                    while True:
                        # Wait for an event on any subscribed topic
                        tasks_q = [asyncio.create_task(q.get()) for q in queues]
                        done, pending = await asyncio.wait(tasks_q, return_when=asyncio.FIRST_COMPLETED)
                        for p in pending:
                            p.cancel()
                        
                        event_msg: A2AMessage = done.pop().result()
                        
                        messages.append({
                            "role": "user", 
                            "content": f"Event received from {event_msg.sender_id} on topic {event_msg.receiver_id}: {event_msg.payload.natural_language}"
                        })
                        
                        # Execute LLM to process event
                        provider_name = getattr(blueprint, "provider", "openai")
                        model_name = getattr(blueprint, "model", "gpt-4o")
                        llm_provider = LLMFactory.get_provider(provider_name, model=model_name)

                        kwargs = {
                            "messages": messages,
                            "temperature": blueprint.temperature
                        }
                        if llm_tool_schemas:
                            kwargs["tools"] = llm_tool_schemas

                        llm_response = await llm_provider.generate(**kwargs)
                        response_message = llm_response.choices[0].message
                        messages.append(self._normalize_message(response_message))

                        # Handle tool calls for daemons (simplified)
                        if response_message.tool_calls:
                            for call in response_message.tool_calls:
                                func_name = call.function.name
                                if func_name in bound_tools:
                                    try:
                                        func_args = json.loads(call.function.arguments)
                                        tool_result = bound_tools[func_name](**func_args)
                                        if inspect.iscoroutine(tool_result):
                                            tool_result = await tool_result
                                        messages.append({
                                            "role": "tool", "tool_call_id": call.id, "name": func_name, "content": json.dumps(tool_result)
                                        })
                                    except Exception as e:
                                        messages.append({
                                            "role": "tool", "tool_call_id": call.id, "name": func_name, "content": f"Error: {e}"
                                        })

                except asyncio.CancelledError:
                    for q, topic in zip(queues, topics):
                        self.blackboard.unsubscribe(topic, q)
                    logger.info("daemon_terminated", agent_id=agent_id)
                    break
                except Exception as e:
                    for q, topic in zip(queues, topics):
                        self.blackboard.unsubscribe(topic, q)
                    logger.error("daemon_crashed", agent_id=agent_id, error=str(e))
                    await asyncio.sleep(5) # Supervisor backoff before restart

    async def _spawn_ephemeral_agent(self, blueprint: AgentBlueprint, task: SubTask, initial_context: Optional[Dict] = None):
        """The isolated lifecycle of a single JIT Agent."""
        with tracer.start_as_current_span(f"agent_lifecycle_{blueprint.agent_id}") as span:
            agent_id = blueprint.agent_id
            span.set_attribute("agent_id", agent_id)
            span.set_attribute("task_id", task.task_id)
            logger.info("agent_spawned", agent_id=agent_id, task_id=task.task_id, is_resume=bool(initial_context))
            
            # 1. DEPENDENCY RESOLUTION (WAIT & HYDRATE)
            context_payloads = []

            # Hydrate Agent History / Memory
            thread_history = await self.blackboard.get_thread_history(thread_ids={task.task_id})
            if getattr(blueprint, "history_limit", None):
                thread_history = thread_history[-blueprint.history_limit:]

            if thread_history:
                history_text = "\n".join([f"[{m.sender_id}] ({m.performative}): {m.payload.natural_language}" for m in thread_history])
                context_payloads.append(f"Historical Context:\n{history_text}")

            if task.dependencies:
                for dep_id in task.dependencies:
                    # Subscribe FIRST to avoid the race condition where the dependency
                    # completes between the history check and the subscribe call.
                    queue = self.blackboard.subscribe(dep_id)

                    # Then check if the result already landed in Redis history.
                    history = await self.blackboard.get_thread_history()
                    completed = [msg for msg in history if msg.receiver_id == dep_id and msg.performative == "inform"]

                    if completed:
                        # Already done — use the most recent result and release the subscription.
                        self.blackboard.unsubscribe(dep_id, queue)
                        message = completed[-1]
                    else:
                        # Not yet done — block until the in-memory publish arrives.
                        message: A2AMessage = await queue.get()
                        self.blackboard.unsubscribe(dep_id, queue)

                    context_payloads.append(f"Result from {dep_id}:\n{message.payload.natural_language}")

            compiled_context = "\n\n".join(context_payloads)
            
            if initial_context and "collected_context" in initial_context:
                compiled_context += f"\n\nPreviously Collected Context:\n{json.dumps(initial_context['collected_context'])}"
            
            execution_prompt = f"Objective: {task.description}\n\nUpstream Context:\n{compiled_context}\n\nTermination Condition: {blueprint.termination_condition}"

            # 2. BIND EXECUTION CONTEXT (IoC)
            bound_tools = self.registry.get_ephemeral_toolkit(blueprint.injected_tools)
            llm_tool_schemas = self.registry.get_ephemeral_schemas(blueprint.injected_tools)

            # Inject request_human_input tool
            llm_tool_schemas.append({
                "type": "function",
                "function": {
                    "name": "request_human_input",
                    "description": "Call this tool when you need explicit human feedback, approval, or input to proceed. It will hibernate the agent instantly and save your context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Why human input is needed (e.g., 'approval', 'clarification')."},
                            "request_message": {"type": "string", "description": "The exact question or prompt to show the human."},
                            "expected_response_type": {"type": "string", "enum": ["boolean", "text", "multiple_choice"], "description": "The format of response you expect."}
                        },
                        "required": ["reason", "request_message", "expected_response_type"]
                    }
                }
            })

            # Inject discover_system_tools tool
            llm_tool_schemas.append({
                "type": "function",
                "function": {
                    "name": "discover_system_tools",
                    "description": "Look up all other available system tools registered in the backend that you do not currently have access to.",
                    "parameters": {"type": "object", "properties": {}}
                }
            })

            messages = []
            if initial_context and "conversation_history" in initial_context:
                # Agent is resuming: Hydrate previous messages
                for msg in initial_context["conversation_history"]:
                    messages.append(msg)

                # Inject the human response as a proper tool result so the LLM sees a
                # complete conversation (tool_call → tool_result) rather than an
                # unanswered request_human_input tool call, which causes API errors.
                if "human_input_response" in initial_context:
                    human_text = initial_context["human_input_response"]
                    # Find the tool_call_id of the last request_human_input call
                    last_tool_call_id = None
                    for msg in reversed(messages):
                        tool_calls = None
                        if isinstance(msg, dict):
                            tool_calls = msg.get("tool_calls") or []
                        elif hasattr(msg, "tool_calls"):
                            tool_calls = msg.tool_calls or []
                        if tool_calls:
                            for tc in tool_calls:
                                name = tc.get("function", {}).get("name") if isinstance(tc, dict) else getattr(getattr(tc, "function", None), "name", None)
                                if name == "request_human_input":
                                    last_tool_call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                                    break
                        if last_tool_call_id:
                            break

                    if last_tool_call_id:
                        # Proper tool result — satisfies the LLM's tool_call/tool_result protocol
                        messages.append({
                            "role": "tool",
                            "tool_call_id": last_tool_call_id,
                            "name": "request_human_input",
                            "content": human_text
                        })
                    else:
                        # Fallback: inject as a user message if we can't find the call id
                        messages.append({
                            "role": "user",
                            "content": f"Human has responded: {human_text}. Continue processing."
                        })
            else:
                # Fresh start
                messages = [
                    {"role": "system", "content": blueprint.persona_prompt},
                    {"role": "user", "content": execution_prompt}
                ]

            # 3. SECURE EXECUTION ROUTER (LLM LOOP)
            import time
            from db import check_budget_exceeded, record_agent_analytics
            import asyncio
            from litellm import completion_cost
            
            start_time = time.time()
            prompt_tokens = 0
            completion_tokens = 0
            total_cost = 0.0
            tools_used = []
            
            # Pre-flight budget check
            if await asyncio.to_thread(check_budget_exceeded, self._user_id, 0.0):
                logger.warning("budget_exceeded", user="dev_user", agent_id=agent_id)
                final_response_text = "ERROR: User budget exceeded. Execution paused."
                messages.append({"role": "assistant", "content": final_response_text})
                failure_message = A2AMessage(
                    message_id=f"msg_{agent_id}_{int(time.time())}",
                    thread_id=task.task_id,
                    sender_id=agent_id,
                    receiver_id=task.task_id,
                    performative="failure",
                    payload=MessagePayload(natural_language=final_response_text),
                    timestamp=time.time()
                )
                await self.blackboard.publish(failure_message)
                return
                
            final_response_text = ""
            max_retries = 3
            retry_count = 0

            while True:
                try:
                    # Execute LLM with STRICT schema boundaries
                    provider_name = getattr(blueprint, "provider", "openai")
                    model_name = getattr(blueprint, "model", "gpt-4o")
                    llm_provider = LLMFactory.get_provider(provider_name, model=model_name)

                    kwargs = {
                        "messages": messages,
                        "temperature": blueprint.temperature
                    }
                    if llm_tool_schemas:
                        kwargs["tools"] = llm_tool_schemas

                    logger.info(
                        "llm_input",
                        agent_id=agent_id,
                        task_id=task.task_id,
                        provider=provider_name,
                        model=model_name,
                        messages=messages,
                    )
                    llm_response = await llm_provider.generate(**kwargs)

                    # Accumulate Cost
                    try:
                        cost = completion_cost(completion_response=llm_response)
                        total_cost += cost
                        prompt_tokens += getattr(llm_response.usage, 'prompt_tokens', 0)
                        completion_tokens += getattr(llm_response.usage, 'completion_tokens', 0)
                        
                        # Check budget mid-flight
                        if await asyncio.to_thread(check_budget_exceeded, self._user_id, cost):
                            logger.warning("budget_exceeded_mid_flight", user="dev_user", agent_id=agent_id)
                            final_response_text = "ERROR: User budget exceeded during execution."
                            break
                    except Exception as e:
                        logger.error("cost_calculation_failed", error=str(e))
                        
                    response_message = llm_response.choices[0].message
                    messages.append(self._normalize_message(response_message))

                    logger.info(
                        "llm_output",
                        agent_id=agent_id,
                        task_id=task.task_id,
                        content=response_message.content,
                        tool_calls=[
                            {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                            for tc in (response_message.tool_calls or [])
                        ],
                    )

                    if response_message.tool_calls:
                        for call in response_message.tool_calls:
                            func_name = call.function.name
                            tools_used.append(func_name)

                            # Handle System Tools
                            if func_name == "discover_system_tools":
                                all_tools = list(self.registry._registry.keys())
                                result_str = f"Available system tools: {all_tools}. To request access to a tool, use `request_human_input`."
                                messages.append({"role": "tool", "tool_call_id": call.id, "name": func_name, "content": result_str})
                                continue

                            # Handle Hibernation (Human-in-the-Loop)
                            if func_name == "request_human_input":
                                try:
                                    func_args = json.loads(call.function.arguments)
                                    reason = func_args.get("reason", "Human input required.")
                                    request_message = func_args.get("request_message", "Please provide input.")
                                    expected_type = func_args.get("expected_response_type", "text")
                                except Exception:
                                    reason = "Human input required."
                                    request_message = "Please provide input."
                                    expected_type = "text"
                                
                                # Prepare serialized history to save.
                                # Use a JSON round-trip to guarantee Redis-safe dicts
                                # even when messages contain nested pydantic objects.
                                def serialize_message(m):
                                    if hasattr(m, 'model_dump'):
                                        raw = m.model_dump()
                                    elif hasattr(m, '__dict__'):
                                        raw = dict(m.__dict__)
                                    elif isinstance(m, dict):
                                        raw = m
                                    else:
                                        raw = str(m)
                                    return json.loads(json.dumps(raw, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o)))

                                safe_messages = [serialize_message(m) for m in messages]

                                agent_state = {
                                    "thread_id": task.task_id,
                                    "original_agent_blueprint": blueprint.model_dump(),
                                    "conversation_history": safe_messages,
                                    "collected_context": {"latest_tool_calls": len(safe_messages)},
                                    "human_input_request": {
                                        "timestamp": int(time.time()),
                                        "reason": reason,
                                        "request_message": request_message,
                                        "expected_response_type": expected_type
                                    }
                                }
                                
                                await self.blackboard.save_agent_state(task.task_id, agent_state)

                                hibernate_msg = A2AMessage(
                                    message_id=f"msg_{agent_id}_{int(time.time())}",
                                    thread_id=task.task_id,
                                    sender_id=agent_id,
                                    receiver_id="human_interface",
                                    performative="hibernate",
                                    payload=MessagePayload(
                                        natural_language=reason,
                                        structured_data={
                                            "type": "human_input_required",
                                            "reason": reason,
                                            "message": request_message,
                                            "response_type": expected_type,
                                            "state_key": f"human_input:{task.task_id}"
                                        }
                                    ),
                                    timestamp=time.time()
                                )
                                logger.info("agent_hibernate", agent_id=agent_id, task_id=task.task_id, reason=reason)
                                # Register as hibernated BEFORE publishing so execute_manifest
                                # doesn't exit the loop before the publish completes.
                                self.hibernated_task_ids.add(task.task_id)
                                await self.blackboard.publish(hibernate_msg)
                                return # Self-destruct and wait for human response unblock

                            # Hardware-level security
                            if func_name not in bound_tools:
                                logger.error("unauthorized_tool_execution", agent_id=agent_id, tool_name=func_name)
                                raise PermissionError(f"Agent {agent_id} attempted unauthorized tool execution: {func_name}")

                            # Execute the bound function pointer
                            try:
                                func_args = json.loads(call.function.arguments)
                                logger.info("tool_input", agent_id=agent_id, tool_name=func_name, arguments=func_args)
                                tool_result = bound_tools[func_name](**func_args)
                                if inspect.iscoroutine(tool_result):
                                    tool_result = await tool_result
                                result_str = json.dumps(tool_result)
                                logger.info("tool_output", agent_id=agent_id, tool_name=func_name, result=tool_result)
                            except Exception as e:
                                result_str = f"Tool execution failed: {str(e)}"
                                logger.error("tool_execution_failed", agent_id=agent_id, tool_name=func_name, error=str(e))

                            # Append tool result to context for the LLM to synthesize
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call.id,
                                "name": func_name,
                                "content": result_str
                            })
                        # Loop continues to let the LLM process the tool outputs
                    else:
                        # No tool calls means the agent has reached its termination state
                        final_response_text = response_message.content
                        break
                except Exception as e:
                    retry_count += 1
                    logger.warning("agent_llm_error", agent_id=agent_id, retry_count=retry_count, error=str(e))
                    if retry_count > max_retries:
                        error_msg = f"Agent failed after {max_retries} retries. Last error: {str(e)}"
                        logger.error("agent_failed", agent_id=agent_id, error=str(e))
                        failure_message = A2AMessage(
                            message_id=f"msg_{agent_id}_{int(time.time())}",
                            thread_id=task.task_id,
                            sender_id=agent_id,
                            receiver_id=task.task_id,
                            performative="failure",
                            payload=MessagePayload(natural_language=error_msg),
                            timestamp=time.time()
                        )
                        await self.blackboard.publish(failure_message)
                        await self.blackboard.publish_to_dlq(failure_message, error_reason=str(e))
                        return
                    await asyncio.sleep(1)

            # 4. PUBLISH TO BLACKBOARD (INFORM)
            result_message = A2AMessage(
                message_id=f"msg_{agent_id}_{int(time.time())}",
                thread_id=task.task_id,
                sender_id=agent_id,
                receiver_id=task.task_id,
                performative="inform",
                payload=MessagePayload(natural_language=final_response_text),
                timestamp=time.time()
            )

            # 5. POST-PROCESSING & ANALYTICS
            lifetime = time.time() - start_time
            await asyncio.to_thread(
                record_agent_analytics,
                task.task_id, agent_id, task.task_id, getattr(blueprint, "provider", "openai"), getattr(blueprint, "model", "gpt-4o"),
                prompt_tokens, completion_tokens, total_cost, tools_used, True, lifetime,
                self._user_id, self._tenant_id
            )

            logger.info("agent_terminated", agent_id=agent_id, task_id=task.task_id, status="success")
            await self.blackboard.publish(result_message)
            # 6. DIE: Function ends, instance context is garbage collected.
