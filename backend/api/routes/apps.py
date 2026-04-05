import uuid
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any

import structlog

from api.routes.auth import get_current_user
from infrastructure import db
from core.globals import state_manager, active_workflow_tasks, blackboard, registry
from engine.compiler import JITCompiler
from core.schemas import WorkflowState, SynthesisManifest, SubTask

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/apps", tags=["apps"])

class AppCreateRequest(BaseModel):
    name: str = Field(..., description="The user-friendly name of the app")
    visual_layout: Dict[str, Any] = Field(default_factory=dict, description="Visual structure of the DAG (ReactFlow state)")
    synthesis_manifest: Dict[str, Any] = Field(..., description="The synthesized manifest containing agent blueprints")

class AppRunRequest(BaseModel):
    provider: str = "google"
    model: str = "gemini-3.1-flash-lite-preview"

@router.get("/")
async def list_apps(user: dict = Depends(get_current_user)):
    """List all saved apps for the user's tenant."""
    # Note: Using tenant_1 as default, if multi-tenant becomes real, use user['tenant_id']
    tenant_id = "tenant_1"
    apps = db.get_apps(tenant_id)
    return apps

@router.get("/{app_id}")
async def get_app(app_id: str, user: dict = Depends(get_current_user)):
    """Get details of a specific app."""
    app = db.get_app_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app

@router.post("/")
async def save_app(request: AppCreateRequest, user: dict = Depends(get_current_user)):
    """Save a new workflow app."""
    app_id = str(uuid.uuid4())
    tenant_id = "tenant_1" 
    
    success = db.save_app(
        app_id=app_id,
        tenant_id=tenant_id,
        name=request.name,
        visual_layout=request.visual_layout,
        synthesis_manifest=request.synthesis_manifest
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save application")
        
    return {"id": app_id, "name": request.name, "status": "saved"}

@router.delete("/{app_id}")
async def delete_app(app_id: str, user: dict = Depends(get_current_user)):
    """Delete a saved app."""
    # Check if app exists
    app = db.get_app_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
        
    success = db.delete_app(app_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete application")
        
    return {"status": "deleted"}

async def deploy_app_task(session_id: str, synthesis_manifest_data: dict, app_name: str, provider: str, model: str):
    """Executes a pre-defined app without going through the MetaAgent."""
    try:
        logger.info("app_run_start", session_id=session_id, app_name=app_name)
        await state_manager.update_status(session_id, "architecting") # Briefly say architecting or preparing

        # Reconstruct SynthesisManifest directly from saved DB dict
        manifest = SynthesisManifest.model_validate(synthesis_manifest_data)
        logger.info("app_manifest_loaded", session_id=session_id, agent_count=len(manifest.blueprints))

        tasks = []
        for bp in manifest.blueprints:
            original_task_id = bp.target_task_id
            bp.target_task_id = f"{session_id}:{original_task_id}"
            bp.dependencies = [f"{session_id}:{dep}" for dep in bp.dependencies]
            
            # Setup defaults for routing
            bp.model = model
            bp.provider = provider
            
            tasks.append(SubTask(
                task_id=bp.target_task_id,
                description=f"Task derived from app blueprint: {bp.agent_id}",
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
        logger.info("app_execution_completed", session_id=session_id)

        await state_manager.update_status(session_id, "completed")
        
        # We need to broadcast the completion since the frontend expects it
        from api.routes.workflows import manager
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "completed",
            "message": f"App '{app_name}' completed successfully."
        })
        
        # Optimize
        from engine.optimization import optimize_blueprints_task
        asyncio.create_task(optimize_blueprints_task(session_id, state_manager, blackboard))

    except Exception as e:
        logger.error("app_run_failed", session_id=session_id, error=str(e))
        await state_manager.update_status(session_id, "failed")
        
        from api.routes.workflows import manager, clean_error_message
        clean_msg = clean_error_message(e)
        await manager.broadcast_to_session(session_id, {
            "type": "notification",
            "performative": "failure",
            "message": clean_msg
        })
    finally:
        if session_id in active_workflow_tasks:
            del active_workflow_tasks[session_id]


@router.post("/{app_id}/run")
async def run_app(app_id: str, request: AppRunRequest, user: dict = Depends(get_current_user)):
    """Run/Deploy an existing app."""
    app = db.get_app_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
        
    synthesis_manifest = app.get("synthesis_manifest")
    if not synthesis_manifest:
        raise HTTPException(status_code=400, detail="App has no valid synthesis manifest")
        
    session_id = str(uuid.uuid4())
    
    initial_state = WorkflowState(
        session_id=session_id,
        user_id=user["user_id"],
        original_objective=f"Running deployed application: {app['name']}",
        tasks=[],
        status="analyzing",
        timestamp=time.time()
    )
    await state_manager.save_state(initial_state)

    # Spawn background task
    task = asyncio.create_task(
        deploy_app_task(
            session_id=session_id,
            synthesis_manifest_data=synthesis_manifest,
            app_name=app["name"],
            provider=request.provider,
            model=request.model
        )
    )
    active_workflow_tasks[session_id] = task
    
    return {
        "session_id": session_id,
        "status": "analyzing",
        "message": f"App '{app['name']}' started successfully."
    }
