"""
REST endpoints for the Deterministic Workflow Engine.
"""

import uuid
import structlog
from fastapi import APIRouter, HTTPException
from core.schemas import DeterministicWorkflowRequest, DeterministicWorkflowResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/deterministic", tags=["deterministic"])


@router.post("/run", response_model=DeterministicWorkflowResponse)
async def run_deterministic_workflow(request: DeterministicWorkflowRequest):
    """
    Generate and execute a typed, sandboxed Python workflow from a natural-language objective.

    A single LLM call generates the pipeline; no LLM is used at runtime.
    Each step is a pure function — validated, schema-checked, and sandboxed.
    """
    from engine.deterministic_workflow import DeterministicWorkflowEngine

    engine = DeterministicWorkflowEngine(provider=request.provider, model=request.model)
    session_id = str(uuid.uuid4())

    try:
        workflow, final_context, trace = engine.generate_and_run(
            objective=request.objective,
            initial_input=request.initial_input,
        )
    except (ValueError, TypeError) as exc:
        logger.warning("deterministic_workflow_validation_error", error=str(exc))
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("deterministic_workflow_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}")

    return DeterministicWorkflowResponse(
        session_id=session_id,
        workflow_steps=[step.model_dump() for step in workflow.workflow],
        execution_trace=trace,
        final_context=final_context,
    )
