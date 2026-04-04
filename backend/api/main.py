# Monkeypatch to handle compatibility issues between FastAPI 0.109.x and Starlette 1.0.0
import starlette.routing
_original_starlette_router_init = starlette.routing.Router.__init__
def _new_starlette_router_init(self, *args, **kwargs):
    on_startup = kwargs.pop("on_startup", None)
    on_shutdown = kwargs.pop("on_shutdown", None)
    _original_starlette_router_init(self, *args, **kwargs)
    if not hasattr(self, "on_startup"):
        self.on_startup = on_startup or []
    if not hasattr(self, "on_shutdown"):
        self.on_shutdown = on_shutdown or []
starlette.routing.Router.__init__ = _new_starlette_router_init

import fastapi.routing
_original_router_init = fastapi.routing.APIRouter.__init__
def _new_router_init(self, *args, **kwargs):
    on_startup = kwargs.pop("on_startup", None)
    on_shutdown = kwargs.pop("on_shutdown", None)
    _original_router_init(self, *args, **kwargs)
    if not hasattr(self, "on_startup"):
        self.on_startup = on_startup or []
    if not hasattr(self, "on_shutdown"):
        self.on_shutdown = on_shutdown or []
fastapi.routing.APIRouter.__init__ = _new_router_init

import os
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.globals import state_manager, blackboard, active_workflow_tasks, registry
from infrastructure import db
from tools.agent_reach_tools import AGENT_REACH_TOOLS
from tools.filesystem_tools import FILESYSTEM_TOOLS
from tools.shell_tools import SHELL_TOOLS
from tools.adapters import LangchainAdapter

from api.routes import auth, workflows, tools as tools_routes
from infrastructure.telemetry import setup_telemetry, get_tracer

setup_telemetry()
logger = structlog.get_logger(__name__)
tracer = get_tracer(__name__)

def register_browser_tools(registry):
    search_tools = []
    try:
        for tool_info in AGENT_REACH_TOOLS:
            registry.register(tool_info["name"], tool_info["func"], tool_info["schema"])
            logger.info("tool_registered", tool=tool_info["name"], source="agent-reach")
    except Exception as e:
        logger.error("agent_reach_tools_failed", reason=str(e))

    try:
        for tool_info in FILESYSTEM_TOOLS:
            registry.register(tool_info["name"], tool_info["func"], tool_info["schema"])
            logger.info("tool_registered", tool=tool_info["name"], source="filesystem")
    except Exception as e:
        logger.error("filesystem_tools_failed", reason=str(e))

    try:
        for tool_info in SHELL_TOOLS:
            registry.register(tool_info["name"], tool_info["func"], tool_info["schema"])
            logger.info("tool_registered", tool=tool_info["name"], source="shell")
    except Exception as e:
        logger.error("shell_tools_failed", reason=str(e))

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

    try:
        from tools.tools import compile_python_tool
        from langchain_core.tools import StructuredTool
        compiler_tool = StructuredTool.from_function(func=compile_python_tool)
        compiler_adapter = LangchainAdapter(tools=[compiler_tool])
        registry.register_adapter(compiler_adapter)
        logger.info("tool_registered", tool="compile_python_tool")
    except ImportError:
        logger.warning("compile_python_tool_skipped", reason="Could not import compile_python_tool from tools.py")

    try:
        from tools.tool_creator import create_tool
        from langchain_core.tools import StructuredTool
        creator_tool = StructuredTool.from_function(func=create_tool)
        registry.register_adapter(LangchainAdapter(tools=[creator_tool]))
        logger.info("tool_registered", tool="create_tool")
    except Exception as e:
        logger.warning("create_tool_skipped", reason=str(e))

def load_dynamic_tools(registry):
    try:
        import agent_tools
        from langchain_core.tools import StructuredTool
        import inspect

        dynamic_tools = []
        for name, func in inspect.getmembers(agent_tools, inspect.isfunction):
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


def load_tools_from_db(registry):
    """Load active agent-created tools from the database and register them at startup."""
    try:
        from infrastructure.db import get_all_agent_tools
        tools = get_all_agent_tools()
        loaded = 0
        for tool in tools:
            if not tool.get("is_active", True):
                continue
            name = tool["name"]
            if name in registry._registry:
                continue  # Built-in or already loaded from agent_tools.py takes precedence
            try:
                namespace = {}
                exec(compile(tool["python_code"], "<db_tool>", "exec"), namespace)
                func = namespace.get(name)
                if func:
                    schema = tool.get("schema_json") or {}
                    registry.register(name, func, schema)
                    loaded += 1
            except Exception as e:
                logger.warning("db_tool_load_failed", tool=name, error=str(e))
        if loaded:
            logger.info("db_tools_loaded", count=loaded)
    except Exception as e:
        logger.warning("load_tools_from_db_failed", error=str(e))

register_browser_tools(registry)
load_dynamic_tools(registry)
load_tools_from_db(registry)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.run_schema_migrations()
    yield
    if active_workflow_tasks:
        logger.info("cancelling_active_tasks", count=len(active_workflow_tasks))
        for task in active_workflow_tasks.values():
            task.cancel()
        await asyncio.gather(*active_workflow_tasks.values(), return_exceptions=True)
    await blackboard.close()
    await state_manager.redis_client.aclose()


app = FastAPI(
    title="Nagent API",
    description="Production-ready API for nagent workflow execution.",
    lifespan=lifespan,
)

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
origins = [origin.strip() for origin in cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workflows.router)
app.include_router(tools_routes.router)

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
else:
    logger.warning("static_dir_missing", message="Static directory 'static' not found. API-only mode.")
