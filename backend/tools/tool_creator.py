"""
Agent-callable tool for creating and persisting new tools at runtime.
Spawned agents can call create_tool() to define new capabilities that are
immediately registered in the global registry and saved to the database for reuse.
"""
import uuid
import inspect
import traceback
from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger(__name__)


def create_tool(
    name: str,
    description: str,
    code: str,
    parameters_schema: Optional[Dict[str, Any]] = None,
    test_kwargs: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Dynamically creates, compiles, and persists a new Python tool. The tool is
    immediately registered in the global registry so all future agents can use it,
    and is saved to the database for persistence across restarts.

    Args:
        name (str): The exact function name defined inside `code`. Must be a valid Python identifier.
        description (str): Human-readable description of what the tool does and when to use it.
        code (str): Complete Python source for the function, including any imports it needs.
        parameters_schema (dict, optional): JSON Schema object describing the function parameters.
            If omitted, a basic schema is auto-inferred from the function signature.
        test_kwargs (dict, optional): Keyword arguments to invoke the function with after compilation
            as a smoke test. If provided and the function raises, the tool is NOT persisted.

    Returns:
        str: A status message indicating success or describing the error.
    """
    # --- 1. Compile and validate ---
    namespace: Dict[str, Any] = {}
    try:
        exec(compile(code, "<agent_tool>", "exec"), namespace)
    except SyntaxError:
        return f"SYNTAX ERROR: Could not compile tool '{name}'.\n{traceback.format_exc()}"
    except Exception:
        return f"COMPILE ERROR: Unexpected error compiling '{name}'.\n{traceback.format_exc()}"

    if name not in namespace:
        return (
            f"ERROR: Function '{name}' not found in compiled namespace. "
            f"Ensure the code defines `def {name}(...):`"
        )

    func = namespace[name]

    # --- 2. Optional smoke test ---
    if test_kwargs is not None:
        try:
            result = func(**test_kwargs)
            logger.info("tool_smoke_test_passed", tool=name, result=str(result)[:200])
        except Exception:
            return (
                f"TEST ERROR: Tool '{name}' compiled but failed during smoke test.\n"
                f"{traceback.format_exc()}"
            )

    # --- 3. Build schema if not provided ---
    if parameters_schema is None:
        parameters_schema = _infer_schema(func, name, description)

    # --- 4. Register in the live global registry ---
    try:
        from core.globals import registry
        registry.register(name, func, parameters_schema)
        logger.info("tool_registered_live", tool=name)
    except Exception as e:
        return f"REGISTRY ERROR: Tool compiled but failed to register: {e}"

    # --- 5. Persist to Modular Skills Directory ---
    try:
        import os
        skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")
        os.makedirs(skills_dir, exist_ok=True)
        file_path = os.path.join(skills_dir, f"{name}.py")
        
        with open(file_path, "w") as f:
            f.write(f'\"\"\"\n{description}\n\"\"\"\n\n')
            f.write(code)
            f.write('\n\n')
            # Export minimal schema info for the loader
            f.write(f'TOOL_NAME = "{name}"\n')
            
        logger.info("tool_persisted_skills_dir", tool=name, path=file_path)
    except Exception as e:
        return (
            f"PARTIAL SUCCESS: Tool '{name}' is active for this session but "
            f"could not be persisted to the filesystem: {e}"
        )

    return (
        f"SUCCESS: Tool '{name}' compiled, registered, and persisted to skills/{name}.py. "
        f"It is immediately available to all agents and will reload on restart."
    )


def _infer_schema(func, name: str, description: str) -> Dict[str, Any]:
    """Builds a minimal OpenAI-compatible function schema from a Python function signature."""
    sig = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required = []

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for param_name, param in sig.parameters.items():
        annotation = param.annotation
        json_type = type_map.get(annotation, "string")
        properties[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
