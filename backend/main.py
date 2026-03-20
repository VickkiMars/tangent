import asyncio
import uuid
import os
import json
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

import structlog
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

import db
from schemas import WorkflowState, SubTask, A2AMessage, MessagePayload, UserSignup, UserLogin, Token, UserResponse
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
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
state_manager = StateManager(redis_url=redis_url)
blackboard = EventBlackboard(redis_url=redis_url)
registry = GlobalToolRegistry()

active_workflow_tasks: set[asyncio.Task] = set()

# --- Auth Configuration ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tangent-super-secret-key-000")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Auth Endpoints ---
@app.post("/auth/signup", response_model=Token)
async def signup(user: UserSignup, request: Request):
    client_ip = request.client.host
    
    # Check IP restriction
    if db.is_ip_restricted(client_ip):
        raise HTTPException(status_code=400, detail="An account has already been created from this IP address.")
    
    # Check if user exists
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    hashed_pwd = get_password_hash(user.password)
    
    success = db.create_user(
        user_id=user_id,
        email=user.email,
        hashed_password=hashed_pwd,
        name=user.name,
        signup_ip=client_ip
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user.")
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = db.get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    access_token = create_access_token(data={"sub": db_user["email"], "user_id": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_me(token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    
    db_user = db.get_user_by_email(email)
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found.")
    
    return {
        "id": db_user["id"],
        "email": db_user["email"],
        "name": db_user["name"],
        "tenant_id": db_user["tenant_id"]
    }

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

def register_browser_tools(registry: GlobalToolRegistry):
    """
    Registers Langchain-based search/research tools.
    All tools are registered via LangchainAdapter so the meta agent can assign
    them to blueprints by name.
    """
    search_tools = []

    # ── Web Search (DuckDuckGo) ───────────────────────────────────────────────
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun(
            name="web_search",
            description="Search the web using DuckDuckGo. Input: a search query string. Returns relevant search result snippets. Use for current events, factual lookups, and general research."
        )
        search_tools.append(search)
        logger.info("tool_registered", tool="web_search")
    except (ImportError, Exception) as e:
        logger.warning("web_search_skipped", reason=str(e))

    # ── Wikipedia ────────────────────────────────────────────────────────────
    try:
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        wiki = WikipediaQueryRun(
            name="wikipedia_search",
            description="Search and retrieve summaries from Wikipedia. Input: a topic or entity name. Returns a concise encyclopedia summary. Use for background knowledge on well-known topics, people, or concepts.",
            api_wrapper=WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=4000)
        )
        search_tools.append(wiki)
        logger.info("tool_registered", tool="wikipedia_search")
    except (ImportError, Exception) as e:
        logger.warning("wikipedia_search_skipped", reason=str(e))

    # ── ArXiv ─────────────────────────────────────────────────────────────────
    try:
        from langchain_community.tools import ArxivQueryRun
        from langchain_community.utilities import ArxivAPIWrapper
        arxiv = ArxivQueryRun(
            name="arxiv_search",
            description="Search academic papers on ArXiv. Input: a research topic or paper title. Returns paper titles, authors, and abstracts. Use for scientific research, technical literature review, and academic citations.",
            api_wrapper=ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=4000)
        )
        search_tools.append(arxiv)
        logger.info("tool_registered", tool="arxiv_search")
    except (ImportError, Exception) as e:
        logger.warning("arxiv_search_skipped", reason=str(e))

    if search_tools:
        adapter = LangchainAdapter(tools=search_tools)
        registry.register_adapter(adapter)
        logger.info("search_tools_registered", count=len(search_tools), tools=[t.name for t in search_tools])

    # ── Core compiler tool ────────────────────────────────────────────────────
    try:
        from tools import compile_python_tool
        from langchain_core.tools import StructuredTool
        compiler_tool = StructuredTool.from_function(func=compile_python_tool)
        compiler_adapter = LangchainAdapter(tools=[compiler_tool])
        registry.register_adapter(compiler_adapter)
        logger.info("tool_registered", tool="compile_python_tool")
    except ImportError:
        logger.warning("compile_python_tool_skipped", reason="Could not import compile_python_tool from tools.py")

def load_dynamic_tools(registry: GlobalToolRegistry):
    """
    Loads auto-generated Python tools from the agent_tools module if it exists.
    """
    try:
        import agent_tools
        from langchain_core.tools import StructuredTool
        import inspect
        
        dynamic_tools = []
        for name, func in inspect.getmembers(agent_tools, inspect.isfunction):
            # Exclude private functions or imported dependencies like 'dumps'
            if not name.startswith("_") and func.__module__ == 'agent_tools':
                tool = StructuredTool.from_function(func=func)
                dynamic_tools.append(tool)
                
        if dynamic_tools:
            adapter = LangchainAdapter(tools=dynamic_tools)
            registry.register_adapter(adapter)
            logger.info("dynamic_tools_loaded", count=len(dynamic_tools), tools=[t.name for t in dynamic_tools])
    except ImportError:
        logger.info("dynamic_tools_skipped", reason="agent_tools.py not found or empty")
    except Exception as e:
        logger.error("dynamic_tools_error", error=str(e))

register_browser_tools(registry)
load_dynamic_tools(registry)


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
# In production, specify your frontend domain in the CORS_ORIGINS environment variable
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
origins = [origin.strip() for origin in cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security ---
API_KEY_NAME = "X-API-Key"
VALID_API_KEY = os.getenv("API_KEY", "nagent-dev-key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_current_user(
    api_key: str = Depends(api_key_header),
    api_key_query: str = Query(None, alias="api_key")
):
    """Basic API Key user management/auth."""
    key = api_key or api_key_query
    if key == VALID_API_KEY:
        return {"user_id": "dev_user"}
    raise HTTPException(status_code=403, detail="Invalid API Key. Please provide X-API-Key header or api_key query param.")

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

class ResumeWorkflowRequest(BaseModel):
    new_objective: str
    provider: str = "google"
    model: str = "gemini-3.1-flash-lite-preview"

# --- Background Task Runner ---
async def execute_workflow_task(session_id: str, objective: str, provider: str = "google", model: str = "gemini-3.1-flash-lite-preview"):
    try:
        logger.info("workflow_start", session_id=session_id, objective=objective)
        # 1. Update status to architecting
        await state_manager.update_status(session_id, "architecting")

        # 2. Architect Workflow directly
        meta_provider = "gemini" if provider == "google" else provider
        meta_agent = MetaAgent(model_name=f"{meta_provider}/{model}")
        available_tools = list(registry._registry.keys())
        # Build name→description map from registered schemas so the meta agent
        # understands what each tool does and can assign them correctly.
        tool_descriptions = {}
        for name, schema in registry._schemas.items():
            func_info = schema.get("function", schema) if isinstance(schema, dict) else {}
            desc = func_info.get("description", "") if isinstance(func_info, dict) else ""
            tool_descriptions[name] = desc
        loop = asyncio.get_event_loop()

        # PROVIDER ROUTING MAP (Shift from prompts to configuration)
        # Using the map to intelligently override what the LLM might hallucinate
        PROVIDER_ROUTING = {
            "extract_text": "gemini-3.1-flash-lite-preview",
            "web_search": "gemini-3.1-flash-lite-preview",
            "compile_python_tool": "gpt-4o",
            "reasoning": "gpt-4o",
            "creative_writing": "claude-3-5-sonnet-latest",
            "default": "gemini-3.1-flash-lite-preview"
        }

        # Generate structural manifest
        manifest = await loop.run_in_executor(
            None, meta_agent.architect_workflow, objective, available_tools, tool_descriptions
        )
        logger.info("workflow_manifest_created", session_id=session_id, agent_count=len(manifest.blueprints))

        # Map Blueprints to SubTasks while enforcing routing overrides
        tasks: List[SubTask] = []
        for bp in manifest.blueprints:
            # Overwrite provider dynamically based on tools required to enforce 
            # infrastructure-level routing over prompt hallucination
            injected = bp.injected_tools
            best_model = PROVIDER_ROUTING["default"]
            best_provider = "google"
            
            if "compile_python_tool" in injected:
                best_model, best_provider = PROVIDER_ROUTING["compile_python_tool"], "openai"
            elif not injected and getattr(bp, "include_history", False):
                # Synthesis or writing tasks (no tools, heavy context reading)
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
        
        # 5. Background Optimization
        from optimization import optimize_blueprints_task
        asyncio.create_task(optimize_blueprints_task(session_id, state_manager, blackboard))

    except Exception as e:
        logger.error("workflow_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")
        
        # Stop publishing to blackboard; send directly as a session notification
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
        raise
    finally:
        current_task = asyncio.current_task()
        if current_task in active_workflow_tasks:
            active_workflow_tasks.remove(current_task)

async def resume_workflow_task(session_id: str, new_objective: str, provider: str, model: str):
    try:
        await state_manager.update_status(session_id, "architecting")
        state = await state_manager.load_state(session_id)
        
        # Gather previous terminal output from blackboard
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
            bp.target_task_id = f"{bp.target_task_id}_resumed"
            # Link to old threads to satisfy DAG
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
        
        from optimization import optimize_blueprints_task
        asyncio.create_task(optimize_blueprints_task(session_id, state_manager, blackboard))
    except Exception as e:
        logger.error("resumption_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")

        # Direct notification instead of blackboard
        clean_msg = clean_error_message(e)
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": clean_msg
        })
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
        status="analyzing",
        timestamp=time.time()
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

@app.get("/workflows")
async def list_workflows(user: dict = Depends(get_current_user)):
    """List all workflow states for the current user's tenant."""
    workflows = await state_manager.list_workflows("tenant_1")
    return workflows

@app.get("/workflows/{session_id}")
async def get_workflow(session_id: str, user: dict = Depends(get_current_user)):
    """Get the current status, tasks, and manifest of a workflow."""
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Filter blackboard history to only include messages belonging to this workflow's
    # tasks, not the global history of all workflows (Bug 15).
    task_ids = {t.task_id for t in state.tasks} if state.tasks else set()
    history = await blackboard.get_thread_history(thread_ids=task_ids)

    from db import get_workflow_analytics
    analytics = []
    if task_ids:
        analytics = await asyncio.to_thread(get_workflow_analytics, list(task_ids))

    return {
        "state": state.model_dump(),
        "logs": [msg.model_dump() for msg in history],
        "analytics": analytics
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

    # The compiler holds the reference to the agent that is hibernating and waiting for input.
    # We can directly unblock it.
    compiler = JITCompiler(blackboard=blackboard, registry=registry)
    await compiler.unblock_agent(request.task_id, request.input)
    return {"status": "success", "message": f"Input submitted for task {request.task_id}"}
    
@app.get("/analytics/costs/summary")
async def get_costs_summary(user: dict = Depends(get_current_user)):
    """API endpoint to get total cost and tokens across the user's entire org."""
    from db import get_global_cost_summary
    import asyncio
    
    summary = await asyncio.to_thread(get_global_cost_summary, "tenant_1")
    return summary

@app.post("/workflows/{session_id}/resume", response_model=WorkflowResponse)
async def resume_workflow(
    session_id: str,
    request: ResumeWorkflowRequest,
    user: dict = Depends(get_current_user)
):
    """Resume a completed thread with new instructions."""
    state = await state_manager.load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if state.status not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot resume an active workflow")
    
    task = asyncio.create_task(resume_workflow_task(session_id, request.new_objective, request.provider, request.model))
    active_workflow_tasks.add(task)
    return WorkflowResponse(session_id=session_id, status="analyzing", message="Resumption started")

# --- WebSockets ---

class ConnectionManager:
    def __init__(self):
        # Mappings of session_id -> list of WebSockets
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
        """Send a message directly to all websocket clients of a specific session."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@app.websocket("/workflows/{session_id}/events")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    api_key: str = Query(None),
):
    """Stream real-time Blackboard events for a specific workflow."""
    if api_key != VALID_API_KEY:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    state = await state_manager.load_state(session_id)
    if not state:
        await websocket.close(code=1008, reason="Workflow not found")
        return

    await manager.connect(session_id, websocket)

    # 1. Immediately check if the workflow already failed (Re-play for new connections)
    if state.status == "failed":
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": "Workflow previously failed. Check your configuration."
        })

    # 2. Subscribe to the "blackboard" broadcast topic for future events.
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

# --- Mount Static Frontend (Served by FastAPI) ---
# Must be registered LAST so API routes take priority over the catch-all SPA mount.
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
else:
    logger.warning("static_dir_missing", message="Static directory 'static' not found. API-only mode.")
