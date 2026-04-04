import os
import uuid
import time
import asyncio
from typing import Dict, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query

from core.globals import state_manager, blackboard, registry, active_workflow_tasks
from core.schemas import WorkflowRequest, WorkflowResponse, HumanInputRequest, ResumeWorkflowRequest, SubTask, A2AMessage, MessagePayload
from api.routes.auth import get_current_user
from engine.meta import MetaAgent
from engine.compiler import JITCompiler

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["workflows"])
VALID_API_KEY = os.getenv("API_KEY", "nagent-dev-key")

def clean_error_message(e: Exception) -> str:
    """Translate technical stack traces into user-friendly notifications."""
    msg = str(e)
    if "API Key" in msg or "API_KEY_INVALID" in msg:
        return "LLM Configuration Error: API Key not found or invalid. Please check your .env settings."
    if "rate limit" in msg.lower():
        return "Service temporarily busy (LLM Rate Limit). Please wait a moment and retry."
    if "BadRequestError" in msg:
        return "LLM Request Failed: Possible malformed prompt or model unavailability."
    if "Insufficient quota" in msg:
        return "LLM Quota Exceeded: Please check your billing/usage limits."
    return f"Fatal Workflow Error: {msg[:100]}"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                ws for ws in self.active_connections[session_id] if ws != websocket
            ]
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

async def execute_workflow_task(session_id: str, objective: str, provider: str = "google", model: str = "gemini-3.1-flash-lite-preview"):
    try:
        logger.info("workflow_start", session_id=session_id, objective=objective)
        await state_manager.update_status(session_id, "architecting")

        meta_provider = "gemini" if provider == "google" else provider
        meta_agent = MetaAgent(model_name=f"{meta_provider}/{model}")
        available_tools = list(registry._registry.keys())
        tool_descriptions = {}
        for name, schema in registry._schemas.items():
            func_info = schema.get("function", schema) if isinstance(schema, dict) else {}
            desc = func_info.get("description", "") if isinstance(func_info, dict) else ""
            tool_descriptions[name] = desc
        loop = asyncio.get_event_loop()

        PROVIDER_ROUTING = {
            "extract_text": "gemini-3.1-flash-lite-preview",
            "web_search": "gemini-3.1-flash-lite-preview",
            "compile_python_tool": "gpt-4o",
            "write_file": "gpt-4o",
            "patch_file": "gpt-4o",
            "run_shell": "gpt-4o",
            "reasoning": "gpt-4o",
            "creative_writing": "claude-3-5-sonnet-latest",
            "default": "gemini-3.1-flash-lite-preview"
        }

        manifest = await loop.run_in_executor(
            None, meta_agent.architect_workflow, objective, available_tools, tool_descriptions
        )
        logger.info("workflow_manifest_created", session_id=session_id, agent_count=len(manifest.blueprints))

        tasks: List[SubTask] = []
        for bp in manifest.blueprints:
            original_task_id = bp.target_task_id
            bp.target_task_id = f"{session_id}:{original_task_id}"
            
            bp.dependencies = [f"{session_id}:{dep}" for dep in bp.dependencies]

            injected = bp.injected_tools
            best_model = PROVIDER_ROUTING["default"]
            best_provider = "google"
            
            if "compile_python_tool" in injected:
                best_model, best_provider = PROVIDER_ROUTING["compile_python_tool"], "openai"
            elif not injected and getattr(bp, "include_history", False):
                best_model, best_provider = PROVIDER_ROUTING["creative_writing"], "anthropic"
                
            bp.model = best_model
            bp.provider = best_provider
            
            tasks.append(SubTask(
                task_id=bp.target_task_id,
                description=f"Task derived from blueprint: {bp.agent_id}",
                required_capabilities=bp.injected_tools,
                dependencies=bp.dependencies,
                provider=bp.provider,
                model=bp.model
            ))

        state = await state_manager.load_state(session_id)
        if state:
            state.manifest = manifest
            state.tasks = tasks
            state.status = "executing"
            await state_manager.save_state(state)

        compiler = JITCompiler(blackboard=blackboard, registry=registry)
        user_id = state.user_id if state else "dev_user"
        await compiler.execute_manifest(manifest, tasks, user_id=user_id)
        logger.info("workflow_execution_completed", session_id=session_id)

        await state_manager.update_status(session_id, "completed")
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "completed",
            "message": "Workflow completed successfully."
        })
        
        from engine.optimization import optimize_blueprints_task
        asyncio.create_task(optimize_blueprints_task(session_id, state_manager, blackboard))

    except Exception as e:
        logger.error("workflow_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")
        
        clean_msg = clean_error_message(e)
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": clean_msg
        })

async def execute_workflow_task_wrapper(session_id: str, objective: str, provider: str, model: str):
    try:
        await execute_workflow_task(session_id, objective, provider, model)
    except asyncio.CancelledError:
        logger.info("workflow_cancelled", session_id=session_id)
        # Update state to failed/cancelled on explicit cancellation
        await state_manager.update_status(session_id, "failed")
        raise
    finally:
        if session_id in active_workflow_tasks:
            del active_workflow_tasks[session_id]

async def resume_workflow_task(session_id: str, new_objective: str, provider: str, model: str):
    try:
        await state_manager.update_status(session_id, "architecting")
        state = await state_manager.load_state(session_id)
        
        task_ids = {t.task_id for t in state.tasks}
        history = await blackboard.get_thread_history(thread_ids=task_ids)
        terminal_messages = [m for m in history if m.performative == "inform"]
        last_results = "\n".join([f"[{m.sender_id}]: {m.payload.natural_language}" for m in terminal_messages[-5:]])
        
        meta_provider = "gemini" if provider == "google" else provider
        meta_agent = MetaAgent(model_name=f"{meta_provider}/{model}")
        available_tools = list(registry._registry.keys())
        tool_descriptions = {}
        for name, schema in registry._schemas.items():
            func_info = schema.get("function", schema) if isinstance(schema, dict) else {}
            desc = func_info.get("description", "") if isinstance(func_info, dict) else ""
            tool_descriptions[name] = desc
        loop = asyncio.get_event_loop()

        combined_objective = f"Previous results: {last_results}\n\nNew instructions: {new_objective}\nOnly architect tasks to fulfill the NEW instructions based on the previous results."
        new_manifest = await loop.run_in_executor(None, meta_agent.architect_workflow, combined_objective, available_tools, tool_descriptions)
        
        new_tasks = []
        terminal_task_ids = list(task_ids)
        
        for bp in new_manifest.blueprints:
            original_task_id = bp.target_task_id
            bp.target_task_id = f"{session_id}:{original_task_id}_resumed"
            
            bp.dependencies = [f"{session_id}:{dep}" for dep in bp.dependencies]
            bp.dependencies = list(set(bp.dependencies + terminal_task_ids))
            
            state.manifest.blueprints.append(bp)
            
            bp.model = model
            bp.provider = "google" if meta_provider == "gemini" else meta_provider
            
            new_tasks.append(SubTask(
                task_id=bp.target_task_id,
                description=f"Resumed Task: {bp.agent_id}",
                required_capabilities=bp.injected_tools,
                dependencies=bp.dependencies,
                provider=bp.provider,
                model=bp.model
            ))
            
        state.tasks.extend(new_tasks)
        state.status = "executing"
        await state_manager.save_state(state)
        
        compiler = JITCompiler(blackboard=blackboard, registry=registry)
        await compiler.execute_manifest(new_manifest, new_tasks)
        await state_manager.update_status(session_id, "completed")
        
        from engine.optimization import optimize_blueprints_task
        asyncio.create_task(optimize_blueprints_task(session_id, state_manager, blackboard))
    except Exception as e:
        logger.error("resumption_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")

        clean_msg = clean_error_message(e)
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": clean_msg
        })
    finally:
        if session_id in active_workflow_tasks:
            del active_workflow_tasks[session_id]

# --- Endpoints ---

@router.post("/workflows", response_model=WorkflowResponse)
async def submit_workflow(
    request: WorkflowRequest,
    user: dict = Depends(get_current_user)
):
    session_id = str(uuid.uuid4())

    from core.schemas import WorkflowState
    initial_state = WorkflowState(
        session_id=session_id,
        user_id=user["user_id"],
        original_objective=request.objective,
        tasks=[],
        status="analyzing",
        timestamp=time.time()
    )
    await state_manager.save_state(initial_state)

    task = asyncio.create_task(execute_workflow_task_wrapper(session_id, request.objective, request.provider, request.model))
    active_workflow_tasks[session_id] = task

    return WorkflowResponse(
        session_id=session_id,
        status="analyzing",
        message="Workflow submitted successfully and is currently being architected."
    )

@router.get("/workflows")
async def list_workflows(user: dict = Depends(get_current_user)):
    workflows = await state_manager.list_workflows("tenant_1", user_id=user["user_id"])
    return workflows

@router.get("/workflows/{session_id}")
async def get_workflow(session_id: str, user: dict = Depends(get_current_user)):
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if state.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    task_ids = {t.task_id for t in state.tasks} if state.tasks else set()
    history = await blackboard.get_thread_history(thread_ids=task_ids)

    from infrastructure.db import get_workflow_analytics
    analytics = []
    if task_ids:
        analytics = await asyncio.to_thread(get_workflow_analytics, list(task_ids))

    return {
        "state": state.model_dump(),
        "logs": [msg.model_dump() for msg in history],
        "analytics": analytics
    }

@router.post("/workflows/{session_id}/input")
async def submit_human_input(
    session_id: str,
    request: HumanInputRequest,
    user: dict = Depends(get_current_user)
):
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if state.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    task_ids = {t.task_id for t in state.tasks}
    if request.task_id not in task_ids:
        raise HTTPException(status_code=400, detail=f"task_id '{request.task_id}' not found in this workflow.")

    compiler = JITCompiler(blackboard=blackboard, registry=registry)
    await compiler.unblock_agent(request.task_id, request.input)
    return {"status": "success", "message": f"Input submitted for task {request.task_id}"}
    
@router.get("/analytics/costs/summary")
async def get_costs_summary(user: dict = Depends(get_current_user)):
    from infrastructure.db import get_global_cost_summary
    summary = await asyncio.to_thread(get_global_cost_summary, "tenant_1")
    return summary

@router.post("/workflows/{session_id}/resume", response_model=WorkflowResponse)
async def resume_workflow(
    session_id: str,
    request: ResumeWorkflowRequest,
    user: dict = Depends(get_current_user)
):
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if state.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if state.status not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot resume an active workflow")
    
    task = asyncio.create_task(resume_workflow_task(session_id, request.new_objective, request.provider, request.model))
    active_workflow_tasks[session_id] = task
    return WorkflowResponse(session_id=session_id, status="analyzing", message="Resumption started")

@router.post("/workflows/{session_id}/cancel")
async def cancel_workflow(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if state.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if session_id in active_workflow_tasks:
        task = active_workflow_tasks[session_id]
        task.cancel()
        logger.info("workflow_cancel_requested", session_id=session_id)
        
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": "Workflow execution was cancelled by the user."
        })
        
        return {"status": "success", "message": "Workflow cancellation requested."}
    else:
        return {"status": "error", "message": "No active task found for this session."}

@router.websocket("/workflows/{session_id}/events")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    api_key: str = Query(None),
):
    if api_key != VALID_API_KEY:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    state = await state_manager.load_state(session_id)
    if not state:
        await websocket.close(code=1008, reason="Workflow not found")
        return

    await manager.connect(session_id, websocket)

    if state.status == "failed":
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": "Workflow previously failed. Check your configuration."
        })

    queue = blackboard.subscribe("blackboard")

    try:
        while True:
            try:
                message: A2AMessage = await asyncio.wait_for(queue.get(), timeout=1.0)
                current_state = await state_manager.load_state(session_id)
                task_ids = {t.task_id for t in current_state.tasks} if current_state and current_state.tasks else set()

                if message.thread_id in task_ids or message.thread_id == session_id:
                    await websocket.send_json(message.model_dump())
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        blackboard.unsubscribe("blackboard", queue)
