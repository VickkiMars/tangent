import uuid
from typing import Optional, Dict, Any, List

import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.routes.auth import get_current_user
from core.globals import registry
from infrastructure import db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

BUILTIN_SOURCES = {"builtin", "filesystem", "langchain"}


# --- Pydantic models ---

class ToolCreate(BaseModel):
    name: str
    description: str
    code: str
    parameters_schema: Optional[Dict[str, Any]] = None
    test_kwargs: Optional[Dict[str, Any]] = None


class ToolApprove(BaseModel):
    approved: bool


class ToolToggle(BaseModel):
    active: bool


# --- Helpers ---

def _registry_tools_as_list() -> List[Dict[str, Any]]:
    """Snapshot the in-memory registry as a list of built-in tool descriptors."""
    result = []
    for name, schema in registry._schemas.items():
        result.append({
            "id": f"builtin_{name}",
            "name": name,
            "source": "builtin",
            "description": _extract_description(schema),
            "schema_json": schema,
            "python_code": None,
            "is_approved": True,
            "is_active": True,
            "created_at": None,
        })
    return result


def _extract_description(schema: Dict[str, Any]) -> str:
    try:
        if "function" in schema:
            return schema["function"].get("description", "")
        return schema.get("description", "")
    except Exception:
        return ""


# --- Endpoints ---

@router.get("")
async def list_tools(current_user: dict = Depends(get_current_user)):
    """
    Returns all tools: built-in (from registry) and agent/manually-created (from DB).
    Built-in tools that have been overridden by a DB tool with the same name are deduplicated
    (DB version wins).
    """
    db_tools = db.get_all_agent_tools()

    # Build a set of names already covered by DB tools so we can skip duplicates
    db_names = {t["name"] for t in db_tools}

    builtin_tools = [t for t in _registry_tools_as_list() if t["name"] not in db_names]

    # Serialize datetime fields
    for t in db_tools:
        if t.get("created_at"):
            t["created_at"] = t["created_at"].isoformat()

    return builtin_tools + db_tools


@router.post("")
async def create_tool_endpoint(payload: ToolCreate, current_user: dict = Depends(get_current_user)):
    """Manually create and persist a new tool (admin/user-initiated)."""
    from tools.tool_creator import create_tool
    result = create_tool(
        name=payload.name,
        description=payload.description,
        code=payload.code,
        parameters_schema=payload.parameters_schema,
        test_kwargs=payload.test_kwargs,
    )
    if result.startswith("SUCCESS"):
        return {"status": "ok", "message": result}
    raise HTTPException(status_code=400, detail=result)


@router.get("/{tool_id}")
async def get_tool(tool_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific tool by ID. For built-in tools, use 'builtin_<name>' as the ID."""
    if tool_id.startswith("builtin_"):
        name = tool_id[len("builtin_"):]
        if name not in registry._schemas:
            raise HTTPException(status_code=404, detail="Built-in tool not found")
        return {
            "id": tool_id,
            "name": name,
            "source": "builtin",
            "description": _extract_description(registry._schemas[name]),
            "schema_json": registry._schemas[name],
            "python_code": None,
            "is_approved": True,
            "is_active": True,
            "created_at": None,
        }

    tool = db.get_agent_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.get("created_at"):
        tool["created_at"] = tool["created_at"].isoformat()
    return tool


@router.post("/{tool_id}/approve")
async def approve_tool(tool_id: str, payload: ToolApprove, current_user: dict = Depends(get_current_user)):
    """Approve or un-approve an agent-created tool."""
    if tool_id.startswith("builtin_"):
        raise HTTPException(status_code=400, detail="Cannot modify built-in tools")
    ok = db.set_agent_tool_approved(tool_id, payload.approved)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool not found or update failed")
    return {"status": "ok", "approved": payload.approved}


@router.post("/{tool_id}/toggle")
async def toggle_tool(tool_id: str, payload: ToolToggle, current_user: dict = Depends(get_current_user)):
    """Enable or disable an agent-created tool without deleting it."""
    if tool_id.startswith("builtin_"):
        raise HTTPException(status_code=400, detail="Cannot modify built-in tools")
    ok = db.set_agent_tool_active(tool_id, payload.active)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool not found or update failed")

    # Reflect the change in the live registry
    tool = db.get_agent_tool_by_id(tool_id)
    if tool:
        name = tool["name"]
        if not payload.active and name in registry._registry:
            del registry._registry[name]
            registry._schemas.pop(name, None)
            logger.info("tool_deactivated_from_registry", tool=name)
        elif payload.active and name not in registry._registry:
            _reload_tool_into_registry(tool)

    return {"status": "ok", "active": payload.active}


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete an agent-created tool and remove it from the registry."""
    if tool_id.startswith("builtin_"):
        raise HTTPException(status_code=400, detail="Cannot delete built-in tools")

    tool = db.get_agent_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    name = tool["name"]
    ok = db.delete_agent_tool(tool_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete tool from database")

    # Remove from live registry
    registry._registry.pop(name, None)
    registry._schemas.pop(name, None)
    logger.info("tool_deleted", tool=name, tool_id=tool_id)

    return {"status": "ok", "deleted": tool_id}


# --- Internal helper ---

def _reload_tool_into_registry(tool: dict):
    """Re-compile and register a tool from its stored code."""
    try:
        namespace: Dict[str, Any] = {}
        exec(compile(tool["python_code"], "<db_tool>", "exec"), namespace)
        func = namespace.get(tool["name"])
        if func:
            registry.register(tool["name"], func, tool.get("schema_json") or {})
            logger.info("tool_reloaded_into_registry", tool=tool["name"])
    except Exception as e:
        logger.error("tool_reload_error", tool=tool["name"], error=str(e))
