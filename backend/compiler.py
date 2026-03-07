import asyncio
import json
import time
import inspect
from typing import List, Dict, Any, Callable
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
                    asyncio.create_task(self._spawn_ephemeral_agent(blueprint, target_task))
        except asyncio.CancelledError:
            self.blackboard.unsubscribe("unblock_agent", queue)

    async def execute_manifest(self, manifest: SynthesisManifest, tasks: List[SubTask]):
        """Compiles and launches all agents concurrently."""
        self.manifest = manifest
        self.tasks = tasks
        self.task_lookup = {task.task_id: task for task in tasks}
        self.agent_tasks = set()

        self.listener_task = asyncio.create_task(self.start_resume_listener(manifest, tasks))

        for blueprint in manifest.blueprints:
            target_task = self.task_lookup[blueprint.target_task_id]
            if getattr(blueprint, "agent_type", "ephemeral") == "daemon":
                agent_thread = asyncio.create_task(self._spawn_daemon_agent(blueprint, target_task))
            else:
                agent_thread = asyncio.create_task(self._spawn_ephemeral_agent(blueprint, target_task))
            self.agent_tasks.add(agent_thread)

        while self.agent_tasks:
            done, pending = await asyncio.wait(self.agent_tasks, return_when=asyncio.FIRST_COMPLETED)
            self.agent_tasks = pending

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
                        messages.append(response_message)
                        
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

    async def _spawn_ephemeral_agent(self, blueprint: AgentBlueprint, task: SubTask):
        """The isolated lifecycle of a single JIT Agent."""
        with tracer.start_as_current_span(f"agent_lifecycle_{blueprint.agent_id}") as span:
            agent_id = blueprint.agent_id
            span.set_attribute("agent_id", agent_id)
            span.set_attribute("task_id", task.task_id)
            logger.info("agent_spawned", agent_id=agent_id, task_id=task.task_id)
            
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
            execution_prompt = f"Objective: {task.description}\n\nUpstream Context:\n{compiled_context}\n\nTermination Condition: {blueprint.termination_condition}"

            # 2. BIND EXECUTION CONTEXT (IoC)
            bound_tools = self.registry.get_ephemeral_toolkit(blueprint.injected_tools)
            llm_tool_schemas = self.registry.get_ephemeral_schemas(blueprint.injected_tools)

            # Inject standard "hibernate" tool
            llm_tool_schemas.append({
                "type": "function",
                "function": {
                    "name": "request_human_input",
                    "description": "Call this tool when you need explicit human feedback, approval, or input to proceed. It will hibernate the agent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "The exact question or input needed from the human."}
                        },
                        "required": ["reason"]
                    }
                }
            })
            
            # Inject publish_intermediate_state
            llm_tool_schemas.append({
                "type": "function",
                "function": {
                    "name": "publish_intermediate_state",
                    "description": "Publish an intermediate state (e.g. propose, critique) without terminating. Useful for multi-turn debates or cyclic workflows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "receiver_id": {"type": "string", "description": "The task_id to send this to, or 'blackboard' for broadcast."},
                            "performative": {"type": "string", "description": "Type of message: 'propose', 'critique', 'inform', etc."},
                            "content": {"type": "string", "description": "The intermediate reasoning or data."}
                        },
                        "required": ["receiver_id", "performative", "content"]
                    }
                }
            })
            
            # Inject spawn_subtask
            llm_tool_schemas.append({
                "type": "function",
                "function": {
                    "name": "spawn_subtask",
                    "description": "Dynamically spawn a new agent to handle a specific subtask at runtime.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "Clear description of the new task."},
                            "tools_needed": {"type": "array", "items": {"type": "string"}, "description": "List of tool names required."}
                        },
                        "required": ["description", "tools_needed"]
                    }
                }
            })

            messages = [
                {"role": "system", "content": blueprint.persona_prompt},
                {"role": "user", "content": execution_prompt}
            ]

            # 3. SECURE EXECUTION ROUTER (LLM LOOP)
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

                    llm_response = await llm_provider.generate(**kwargs)
                    response_message = llm_response.choices[0].message
                    messages.append(response_message)

                    if response_message.tool_calls:
                        for call in response_message.tool_calls:
                            func_name = call.function.name

                            # Handle Hibernation
                            if func_name == "request_human_input":
                                try:
                                    func_args = json.loads(call.function.arguments)
                                    reason = func_args.get("reason", "Human input required.")
                                except Exception:
                                    reason = "Human input required."

                                hibernate_msg = A2AMessage(
                                    message_id=f"msg_{agent_id}_{int(time.time())}",
                                    thread_id=task.task_id,
                                    sender_id=agent_id,
                                    receiver_id=task.task_id,
                                    performative="hibernate",
                                    payload=MessagePayload(natural_language=reason),
                                    timestamp=time.time()
                                )
                                logger.info("agent_hibernate", agent_id=agent_id, task_id=task.task_id, reason=reason)
                                await self.blackboard.publish(hibernate_msg)
                                return # Self-destruct and wait for unblock

                            if func_name == "publish_intermediate_state":
                                try:
                                    func_args = json.loads(call.function.arguments)
                                    receiver_id = func_args.get("receiver_id", "blackboard")
                                    performative = func_args.get("performative", "inform")
                                    content = func_args.get("content", "")
                                    msg = A2AMessage(
                                        message_id=f"msg_{agent_id}_{int(time.time())}",
                                        thread_id=task.task_id,
                                        sender_id=agent_id,
                                        receiver_id=receiver_id,
                                        performative=performative,
                                        payload=MessagePayload(natural_language=content),
                                        timestamp=time.time()
                                    )
                                    await self.blackboard.publish(msg)
                                    result_str = "Intermediate state published successfully."
                                except Exception as e:
                                    result_str = f"Failed to publish intermediate state: {e}"
                                messages.append({"role": "tool", "tool_call_id": call.id, "name": func_name, "content": result_str})
                                continue

                            if func_name == "spawn_subtask":
                                try:
                                    func_args = json.loads(call.function.arguments)
                                    description = func_args.get("description", "Dynamic task")
                                    tools_needed = func_args.get("tools_needed", [])
                                    new_task_id = f"dynamic_task_{int(time.time())}"
                                    new_task = SubTask(
                                        task_id=new_task_id,
                                        description=description,
                                        required_capabilities=tools_needed,
                                        dependencies=[],
                                        provider=getattr(blueprint, "provider", "openai"),
                                        model=getattr(blueprint, "model", "gpt-4o")
                                    )
                                    new_blueprint = AgentBlueprint(
                                        agent_id=f"agent_{new_task_id}",
                                        target_task_id=new_task_id,
                                        agent_type="ephemeral",
                                        persona_prompt="You are a dynamically spawned sub-agent.",
                                        injected_tools=tools_needed,
                                        termination_condition="Provide the final result.",
                                        provider=getattr(blueprint, "provider", "openai"),
                                        model=getattr(blueprint, "model", "gpt-4o")
                                    )
                                    
                                    if hasattr(self, 'manifest') and hasattr(self, 'tasks') and hasattr(self, 'task_lookup') and hasattr(self, 'agent_tasks'):
                                        self.manifest.blueprints.append(new_blueprint)
                                        self.tasks.append(new_task)
                                        self.task_lookup[new_task_id] = new_task
                                        agent_thread = asyncio.create_task(self._spawn_ephemeral_agent(new_blueprint, new_task))
                                        self.agent_tasks.add(agent_thread)
                                        result_str = f"Successfully spawned subtask. task_id: {new_task_id}"
                                    else:
                                        result_str = "Error: JITCompiler is not configured for dynamic spawning."
                                except Exception as e:
                                    result_str = f"Failed to spawn subtask: {e}"
                                messages.append({"role": "tool", "tool_call_id": call.id, "name": func_name, "content": result_str})
                                continue

                            # Hardware-level security
                            if func_name not in bound_tools:
                                logger.error("unauthorized_tool_execution", agent_id=agent_id, tool_name=func_name)
                                raise PermissionError(f"Agent {agent_id} attempted unauthorized tool execution: {func_name}")

                            # Execute the bound function pointer
                            try:
                                func_args = json.loads(call.function.arguments)
                                tool_result = bound_tools[func_name](**func_args)
                                if inspect.iscoroutine(tool_result):
                                    tool_result = await tool_result
                                result_str = json.dumps(tool_result)
                                logger.info("tool_executed", agent_id=agent_id, tool_name=func_name)
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

            logger.info("agent_terminated", agent_id=agent_id, task_id=task.task_id, status="success")
            await self.blackboard.publish(result_message)
            # 5. DIE: Function ends, instance context is garbage collected.
