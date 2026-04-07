"""
Deterministic workflow tool — callable by spawned agents.

Wraps DeterministicWorkflowEngine so any agent with this tool injected can
generate and execute a sandboxed pure-function pipeline in a single call.
"""

import json
import structlog

logger = structlog.get_logger(__name__)


def generate_deterministic_workflow(objective: str, initial_input: str) -> str:
    """
    Generate and execute a deterministic, sandboxed Python data-processing pipeline
    via a single LLM call. No LLM is used at runtime — only pure Python functions.

    Use this for tasks that are pure data transformations: extracting and aggregating
    numbers from text, scoring or ranking structured data, multi-step math, format
    conversion, normalisation, or any computation expressible as a typed pipeline.

    Do NOT use this for tasks requiring web search, file I/O, external APIs, or
    LLM-based judgment at each step.

    Args:
        objective: A concise description of what the pipeline should compute.
                   Example: "Extract all integers from the text and return their sum and count."
        initial_input: A JSON-encoded dict of the starting data.
                       Keys and values must be plain Python types (str, int, float, list, dict).
                       Example: '{"text": "prices: 10, 20, 30"}'

    Returns:
        JSON string containing:
          - workflow_steps: the generated pure-function steps (name, input/output schemas, code)
          - execution_trace: per-step input and output
          - final_context: the accumulated dict after all steps run
    """
    from engine.deterministic_workflow import DeterministicWorkflowEngine

    try:
        input_data: dict = json.loads(initial_input)
    except (json.JSONDecodeError, TypeError) as exc:
        return json.dumps({"error": f"initial_input must be a valid JSON string: {exc}"})

    if not isinstance(input_data, dict):
        return json.dumps({"error": "initial_input must be a JSON object (dict), not a list or primitive"})

    engine = DeterministicWorkflowEngine()

    try:
        workflow, final_context, trace = engine.generate_and_run(objective, input_data)
    except (ValueError, TypeError) as exc:
        return json.dumps({"error": f"Validation or execution failed: {exc}"})
    except Exception as exc:
        logger.error("generate_deterministic_workflow_failed", error=str(exc))
        return json.dumps({"error": f"Workflow generation failed: {exc}"})

    return json.dumps({
        "workflow_steps": [step.model_dump() for step in workflow.workflow],
        "execution_trace": trace,
        "final_context": final_context,
    })
