"""
Deterministic Workflow Engine
==============================
Generates and executes a typed, sandboxed Python pipeline via a single LLM call.
No LLM is used at runtime — only pure functions compiled from the generated code.

Contract
--------
- Every step is a pure function that returns a dict
- output_schema of step N must exactly equal input_schema of step N+1
- Allowed types: int, float, str, list[int], list[str], dict[str,float], dict[str,int]
- Code runs in a restricted namespace (SAFE_GLOBALS)
- Forbidden constructs are rejected before compilation
"""

import json
import structlog
from typing import Any, Dict, List, Tuple

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Allowed types
# ---------------------------------------------------------------------------
ALLOWED_TYPES = {"int", "float", "str", "list[int]", "list[str]", "dict[str, float]", "dict[str, int]"}

# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------
FORBIDDEN = [
    "import os", "import sys", "import subprocess", "import shutil",
    "open(", "exec(", "eval(", "__import__", "globals()", "locals()",
    "getattr(", "setattr(", "delattr(",
]

SAFE_GLOBALS: Dict[str, Any] = {
    "__builtins__": {
        "range": range,
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "isinstance": isinstance,
        "print": print,
    }
}


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_type_string(type_str: str, field: str) -> None:
    if type_str not in ALLOWED_TYPES:
        raise ValueError(
            f"Field '{field}' has unsupported type '{type_str}'. "
            f"Allowed: {sorted(ALLOWED_TYPES)}"
        )


def validate_schema(data: dict, schema: dict) -> None:
    """Raise ValueError/TypeError if data does not match schema."""
    for key, expected in schema.items():
        if key not in data:
            raise ValueError(f"Missing key: '{key}'")

        value = data[key]

        if expected == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"'{key}' must be int, got {type(value).__name__}")
        elif expected == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"'{key}' must be float, got {type(value).__name__}")
        elif expected == "str":
            if not isinstance(value, str):
                raise TypeError(f"'{key}' must be str, got {type(value).__name__}")
        elif expected == "list[int]":
            if not isinstance(value, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in value):
                raise TypeError(f"'{key}' must be list[int]")
        elif expected == "list[str]":
            if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
                raise TypeError(f"'{key}' must be list[str]")
        elif expected == "dict[str, float]":
            if not isinstance(value, dict) or not all(
                isinstance(k, str) and isinstance(v, (int, float)) and not isinstance(v, bool)
                for k, v in value.items()
            ):
                raise TypeError(f"'{key}' must be dict[str, float]")
        elif expected == "dict[str, int]":
            if not isinstance(value, dict) or not all(
                isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool)
                for k, v in value.items()
            ):
                raise TypeError(f"'{key}' must be dict[str, int]")


def validate_workflow(workflow) -> None:
    """
    Validate schema chaining across all steps.
    Raises ValueError if output_schema of step N != input_schema of step N+1.
    """
    steps = workflow.workflow
    for i in range(len(steps) - 1):
        out_schema = steps[i].output_schema
        next_in_schema = steps[i + 1].input_schema
        if out_schema != next_in_schema:
            raise ValueError(
                f"Schema mismatch between step '{steps[i].name}' and '{steps[i + 1].name}': "
                f"{out_schema} != {next_in_schema}"
            )

    # Validate all type strings
    for step in steps:
        for field, type_str in {**step.input_schema, **step.output_schema}.items():
            _validate_type_string(type_str, field)


def check_code_safety(code: str) -> None:
    """Raise ValueError if code contains any forbidden constructs."""
    for bad in FORBIDDEN:
        if bad in code:
            raise ValueError(f"Unsafe code detected: '{bad}'")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _compile_step_function(code: str):
    """Compile and return the callable from the step's code string."""
    check_code_safety(code)
    local_env: Dict[str, Any] = {}
    # Allow `import re` specifically since it's commonly needed for text processing
    safe_globals = dict(SAFE_GLOBALS)
    if "import re" in code:
        import re as _re
        safe_globals["__builtins__"] = dict(safe_globals["__builtins__"])  # type: ignore
        safe_globals["re"] = _re
        # Strip the import line so exec doesn't try to re-import under restricted builtins
        code = "\n".join(line for line in code.splitlines() if line.strip() != "import re")
    exec(compile(code, "<workflow_step>", "exec"), safe_globals, local_env)
    callables = [v for v in local_env.values() if callable(v)]
    if not callables:
        raise ValueError("Step code did not define a callable function")
    func = callables[0]
    return func  # type: ignore[return-value]


def run_workflow(
    workflow,
    initial_input: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Execute the workflow sequentially.

    Returns:
        (final_context, execution_trace)
        final_context: accumulated dict after all steps
        execution_trace: list of {step, input, output} per step
    """
    context = dict(initial_input)
    trace: List[Dict[str, Any]] = []

    for step in workflow.workflow:
        func = _compile_step_function(step.code)

        # Slice only the keys this step expects
        input_data: Dict[str, Any] = {k: context[k] for k in step.input_schema if k in context}  # type: ignore[index]

        # Validate input
        validate_schema(input_data, step.input_schema)

        # Execute
        output = func(**input_data)

        if not isinstance(output, dict):
            raise TypeError(f"Step '{step.name}' must return a dict, got {type(output).__name__}")

        # Validate output
        validate_schema(output, step.output_schema)

        trace.append({"step": step.name, "input": input_data, "output": output})

        # Merge into running context
        context.update(output)

    return context, trace


# ---------------------------------------------------------------------------
# Engine (LLM generation + execution)
# ---------------------------------------------------------------------------

WORKFLOW_SYSTEM_PROMPT = """\
You are a code generation engine. Given an objective and an initial input schema, \
generate a deterministic Python workflow as a JSON object.

Rules (non-negotiable):
1. Each step is a pure function — no side effects, no I/O, no network calls.
2. The function MUST return a plain dict whose keys exactly match output_schema.
3. output_schema of step N must equal input_schema of step N+1.
4. Allowed types ONLY: int, float, str, list[int], list[str], dict[str, float], dict[str, int]
5. Functions may use: range, len, sum, min, max, abs, round, sorted, enumerate, zip, map, filter, \
list, dict, str, int, float, bool, isinstance, print, and `import re` (text only).
6. NO other imports. NO os, sys, subprocess, open, exec, eval, __import__, getattr/setattr/delattr.

Output format (JSON only, no markdown, no explanation):
{
  "workflow": [
    {
      "name": "<snake_case_function_name>",
      "description": "<one line>",
      "input_schema": {"field": "type"},
      "output_schema": {"field": "type"},
      "code": "<def function_name(...) -> dict:\\n    ...>"
    }
  ]
}
"""


class DeterministicWorkflowEngine:
    """
    Single-call LLM workflow generator and executor.

    Usage:
        engine = DeterministicWorkflowEngine()
        workflow, final_context, trace = engine.generate_and_run(
            objective="sum integers from text",
            initial_input={"text": "values: 10, 20, 30"}
        )
    """

    def __init__(self, provider: str = "openai", model: str = "gpt-4o"):
        self.provider = provider
        self.model = model

    def generate_and_run(
        self,
        objective: str,
        initial_input: Dict[str, Any],
        provider: str | None = None,
        model: str | None = None,
    ):
        """
        Generate a workflow for the given objective, validate it, and execute it.

        Returns:
            (workflow, final_context, execution_trace)
        """
        import litellm
        from core.schemas import DeterministicWorkflow, WorkflowStep

        provider = provider or self.provider
        model = model or self.model

        # Build the initial input schema from the actual data
        input_schema_description = {
            k: _python_type_to_schema_type(v) for k, v in initial_input.items()
        }

        user_prompt = (
            f"Objective: {objective}\n\n"
            f"Initial input: {json.dumps(initial_input)}\n"
            f"Initial input schema: {json.dumps(input_schema_description)}\n\n"
            "Generate the minimal workflow (2-5 steps) that transforms this input to achieve the objective."
        )

        litellm_model = f"{provider}/{model}" if provider not in ("openai",) else model
        response = litellm.completion(
            model=litellm_model,
            messages=[
                {"role": "system", "content": WORKFLOW_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        logger.info("workflow_generated", objective=objective, raw_length=len(raw or ""))

        try:
            workflow_dict = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        # Parse into typed model
        try:
            steps = [WorkflowStep(**s) for s in workflow_dict.get("workflow", [])]
            workflow = DeterministicWorkflow(workflow=steps)
        except Exception as exc:
            raise ValueError(f"Workflow schema parse error: {exc}") from exc

        if not workflow.workflow:
            raise ValueError("LLM returned an empty workflow")

        # Validate schema chaining
        validate_workflow(workflow)

        # Execute
        final_context, trace = run_workflow(workflow, initial_input)

        logger.info(
            "workflow_executed",
            steps=len(workflow.workflow),
            output_keys=list(final_context.keys()),
        )
        return workflow, final_context, trace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _python_type_to_schema_type(value: Any) -> str:
    """Infer a schema type string from a Python value."""
    if isinstance(value, bool):
        return "str"  # booleans don't have a schema type; treat as str
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        if value and all(isinstance(i, int) for i in value):
            return "list[int]"
        return "list[str]"
    if isinstance(value, dict):
        if value and all(isinstance(v, float) for v in value.values()):
            return "dict[str, float]"
        if value and all(isinstance(v, int) for v in value.values()):
            return "dict[str, int]"
        return "str"
    return "str"
