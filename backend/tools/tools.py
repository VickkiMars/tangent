import json
from typing import Optional, Dict, Any
import sys
import traceback

def compile_python_tool(code_string: str, tool_name: str, test_kwargs: Optional[Dict[str, Any]] = None) -> str:
    """
    Dynamically compiles and registers a Python function as a tool. Use this to handle 
    complex logic, custom data processing, or creating new capabilities during a build task.
    
    Args:
        code_string (str): The raw Python code containing the function definition. Ensure proper indentation.
        tool_name (str): The exact name of the primary function inside `code_string` to execute.
        test_kwargs (dict, optional): A dictionary of arguments to test the function immediately after compilation.
        
    Returns:
        str: Success message or the compilation/execution traceback if it failed.
    """
    try:
        # Create an isolated namespace for the function execution
        namespace = {}
        
        # Compile and execute the function into the namespace
        exec(code_string, namespace)
        
        if tool_name not in namespace:
            return f"ERROR: The function '{tool_name}' was not found in the compiled namespace. Ensure your code defines `def {tool_name}(...):`"
            
        func = namespace[tool_name]
        
        
        # Persist to agent_tools.py on success
        import os
        tools_path = os.path.join(os.path.dirname(__file__), "agent_tools.py")
        if not os.path.exists(tools_path):
            with open(tools_path, "w") as f:
                f.write("# Auto-generated Meta-Orchestrator Tools\nimport json\nimport requests\nfrom typing import *\n\n")
        with open(tools_path, "a") as f:
            f.write(f"\n\n# --- Automatically Generated Tool: {tool_name} ---\n")
            f.write(code_string)
            f.write("\n")

        if test_kwargs:
            result = func(**test_kwargs)
            return f"SUCCESS: Tool compiled, persisted to agent_tools.py, and executed successfully. Test result: {result}"
        
        return f"SUCCESS: Tool '{tool_name}' compiled and persisted to agent_tools.py ready for discovery."
        
    except SyntaxError as e:
        return f"SYNTAX ERROR: Failed to compile.\n{traceback.format_exc()}"
    except Exception as e:
        return f"EXECUTION ERROR: Failed during runtime test.\n{traceback.format_exc()}"
