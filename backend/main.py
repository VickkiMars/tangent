import asyncio
import uuid
import json
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

import structlog
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
 
from schemas import WorkflowState, SubTask, A2AMessage, MessagePayload
from state_manager import StateManager
from blackboard import EventBlackboard
from registry import GlobalToolRegistry
from compiler import JITCompiler
from meta import MetaAgent
from adapters import LangchainAdapter
from telemetry import setup_telemetry, get_tracer

# Telemetry setup disabled to prevent ConnectionRefusedError when OTLP collector is not running
# setup_telemetry()
logger = structlog.get_logger(__name__)
tracer = get_tracer(__name__)

# Initialize Core Services
redis_url = "redis://localhost:6379/0"
state_manager = StateManager(redis_url=redis_url)
blackboard = EventBlackboard(redis_url=redis_url)
registry = GlobalToolRegistry()

# Track active tasks for clean shutdown
active_workflow_tasks: set[asyncio.Task] = set()

def register_browser_tools(registry: GlobalToolRegistry):
    """
    Registers browser/search tools.
    Modify this function to change search providers or browser configuration.
    """
    try:
        # Using DuckDuckGo as the default search provider
        from langchain_community.tools import DuckDuckGoSearchRun
        
        # You can configure the search tool here (e.g., region, time, etc.)
        search = DuckDuckGoSearchRun()
        
        # Wrap in adapter and register
        adapter = LangchainAdapter(tools=[search])
        registry.register_adapter(adapter)
        logger.info("browser_tools_registered", tools=["duckduckgo_search"])
    except ImportError:
        logger.warning("browser_tools_skipped", reason="langchain_community or duckduckgo-search not installed")
    except Exception as e:
        logger.error("browser_tools_error", error=str(e))

register_browser_tools(registry)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Cancel active tasks to prevent hanging on shutdown
    if active_workflow_tasks:
        logger.info("cancelling_active_tasks", count=len(active_workflow_tasks))
        for task in active_workflow_tasks:
            task.cancel()
        await asyncio.gather(*active_workflow_tasks, return_exceptions=True)
    # Cleanly close Redis connections on shutdown (Bug 3)
    await blackboard.close()
    await state_manager.redis_client.aclose()


app = FastAPI(
    title="Nagent API",
    description="Production-ready API for nagent workflow execution.",
    lifespan=lifespan,
)
# FastAPIInstrumentor.instrument_app(app)

# --- CORS Middleware (Essential for Frontend Communication) ---
origins = ["*"]  # In production, replace with specific frontend domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security ---
API_KEY_NAME = "X-API-Key"
VALID_API_KEY = "nagent-dev-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_current_user(api_key: str = Depends(api_key_header)):
    """Basic API Key user management/auth."""
    if api_key == VALID_API_KEY:
        return {"user_id": "dev_user"}
    raise HTTPException(status_code=403, detail="Invalid API Key. Please provide X-API-Key header.")

# --- Models ---
class WorkflowRequest(BaseModel):
    objective: str
    provider: str = "google"
    model: str = "gemini-1.5-flash"

class WorkflowResponse(BaseModel):
    session_id: str
    status: str
    message: str

class HumanInputRequest(BaseModel):
    task_id: str
    input: str

# --- Background Task Runner ---
async def execute_workflow_task(session_id: str, objective: str, provider: str = "google", model: str = "gemini-1.5-flash"):
    try:
        logger.info("workflow_start", session_id=session_id, objective=objective)
        # 1. Update status to architecting
        await state_manager.update_status(session_id, "architecting")

        # 2. Architect Workflow
        # MetaAgent uses the synchronous OpenAI client. Run it in a thread-pool executor
        # so it does not block the async event loop (Bug 14).
        meta_agent = MetaAgent(model_name=f"{provider}/{model}")
        available_tools = list(registry._registry.keys())
        loop = asyncio.get_event_loop()
        
        # Evaluate complexity first
        evaluation = await loop.run_in_executor(
            None, meta_agent.evaluate_complexity, objective
        )
        
        if not evaluation.requires_swarm:
            logger.info("workflow_simple_response", session_id=session_id)
            # Simple task, single LLM response
            response_text = evaluation.direct_response or evaluation.reasoning
            msg = A2AMessage(
                message_id=f"msg_meta_{int(time.time())}",
                thread_id="meta_thread",
                sender_id="meta_agent",
                receiver_id="blackboard",
                performative="inform",
                payload=MessagePayload(natural_language=response_text),
                timestamp=time.time()
            )
            await blackboard.publish(msg)
            
            # Create a dummy task so frontend can display it
            dummy_task = SubTask(
                task_id="meta_thread",
                description=objective,
                required_capabilities=[],
                dependencies=[],
                provider=provider,
                model=model
            )
            state = await state_manager.load_state(session_id)
            if state:
                state.tasks = [dummy_task]
                state.status = "completed"
                await state_manager.save_state(state)
            return

        manifest = await loop.run_in_executor(
            None, meta_agent.architect_workflow, objective, available_tools
        )
        logger.info("workflow_manifest_created", session_id=session_id, agent_count=len(manifest.blueprints))

        # Map Blueprints to SubTasks (as MetaAgent currently only outputs Blueprints)
        tasks: List[SubTask] = []
        for bp in manifest.blueprints:
            tasks.append(SubTask(
                task_id=bp.target_task_id,
                description=f"Task derived from blueprint: {bp.agent_id}",
                required_capabilities=bp.injected_tools,
                dependencies=bp.dependencies,
                provider=bp.provider,
                model=bp.model
            ))

        # Update State
        state = await state_manager.load_state(session_id)
        if state:
            state.manifest = manifest
            state.tasks = tasks
            state.status = "executing"
            await state_manager.save_state(state)

        # 3. JIT Compilation & Execution
        compiler = JITCompiler(blackboard=blackboard, registry=registry)
        await compiler.execute_manifest(manifest, tasks)
        logger.info("workflow_execution_completed", session_id=session_id)

        # 4. Mark Completed
        await state_manager.update_status(session_id, "completed")

    except Exception as e:
        logger.error("workflow_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")

async def execute_workflow_task_wrapper(session_id: str, objective: str, provider: str, model: str):
    try:
        await execute_workflow_task(session_id, objective, provider, model)
    except asyncio.CancelledError:
        logger.info("workflow_cancelled", session_id=session_id)
        raise
    finally:
        current_task = asyncio.current_task()
        if current_task in active_workflow_tasks:
            active_workflow_tasks.remove(current_task)

# --- Endpoints ---

@app.post("/workflows", response_model=WorkflowResponse)
async def submit_workflow(
    request: WorkflowRequest,
    user: dict = Depends(get_current_user)
):
    """Submit a new objective to create and start a workflow."""
    session_id = str(uuid.uuid4())

    # Initialize state
    initial_state = WorkflowState(
        session_id=session_id,
        original_objective=request.objective,
        tasks=[],
        status="analyzing"
    )
    await state_manager.save_state(initial_state)

    # Fire off background task
    task = asyncio.create_task(execute_workflow_task_wrapper(session_id, request.objective, request.provider, request.model))
    active_workflow_tasks.add(task)

    return WorkflowResponse(
        session_id=session_id,
        status="analyzing",
        message="Workflow submitted successfully and is currently being architected."
    )

@app.get("/workflows/{session_id}")
async def get_workflow(session_id: str, user: dict = Depends(get_current_user)):
    """Get the current status, tasks, and manifest of a workflow."""
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Filter blackboard history to only include messages belonging to this workflow's
    # tasks, not the global history of all workflows (Bug 15).
    task_ids = {t.task_id for t in state.tasks} if state.tasks else None
    history = await blackboard.get_thread_history(thread_ids=task_ids)

    return {
        "state": state.model_dump(),
        "logs": [msg.model_dump() for msg in history]
    }

@app.post("/workflows/{session_id}/input")
async def submit_human_input(
    session_id: str,
    request: HumanInputRequest,
    user: dict = Depends(get_current_user)
):
    """Submit human input to unblock a hibernated agent (Bug 6).
    The task_id must match the thread_id of the hibernated agent."""
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    task_ids = {t.task_id for t in state.tasks}
    if request.task_id not in task_ids:
        raise HTTPException(status_code=400, detail=f"task_id '{request.task_id}' not found in this workflow.")

    unblock_msg = A2AMessage(
        message_id=f"msg_human_{int(time.time())}",
        thread_id=request.task_id,
        sender_id="human",
        receiver_id="unblock_agent",
        performative="inform",
        payload=MessagePayload(natural_language=request.input),
        timestamp=time.time()
    )
    await blackboard.publish(unblock_msg)
    return {"status": "input submitted", "task_id": request.task_id}

# --- WebSockets ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/workflows/{session_id}/events")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    api_key: str = Query(None),  # Auth via query param since WS headers are browser-restricted (Bug 13)
):
    """Stream real-time Blackboard events for a specific workflow."""
    if api_key != VALID_API_KEY:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    state = await state_manager.load_state(session_id)
    if not state:
        await websocket.close(code=1008, reason="Workflow not found")
        return

    await manager.connect(websocket)

    # Subscribe to the "blackboard" broadcast topic, which receives a copy of every
    # agent message (Bug 11 — the old "system_events" topic had no publisher).
    queue = blackboard.subscribe("blackboard")

    try:
        while True:
            try:
                message: A2AMessage = await asyncio.wait_for(queue.get(), timeout=1.0)

                # Reload state to pick up tasks that may have been added after connection (Bug 12).
                current_state = await state_manager.load_state(session_id)
                task_ids = {t.task_id for t in current_state.tasks} if current_state and current_state.tasks else None

                # Only forward events that belong to this session's tasks.
                if task_ids is None or message.thread_id in task_ids:
                    await websocket.send_json(message.model_dump())

            except asyncio.TimeoutError:
                # Heartbeat interval — keeps the connection alive and checks for client disconnect.
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        blackboard.unsubscribe("blackboard", queue)
