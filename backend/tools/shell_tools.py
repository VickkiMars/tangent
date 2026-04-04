import subprocess
import os
import shlex

def run_shell(command: str) -> str:
    """
    Execute a shell command and return its output. 
    Use this for running tests (pytest), git commands, or linters.
    Dangerous commands (rm -rf /, etc.) are blocked.
    """
    # Basic safety check
    forbidden = ["rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:"]
    for f in forbidden:
        if f in command:
            return f"Error: Command '{command}' contains forbidden sequence '{f}'."

    try:
        # We use shlex.split for safer handling of arguments
        args = shlex.split(command)
        
        # Determine working directory - defaults to AGENT_WORKSPACE if set
        cwd = os.getenv("AGENT_WORKSPACE", os.getcwd())
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout for safety
            cwd=cwd
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
            
        if result.returncode != 0:
            return f"Command failed with return code {result.returncode}.\nOutput: {output}"
            
        return output if output else "Command executed successfully (no output)."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

SHELL_TOOLS = [
    {
        "name": "run_shell",
        "func": run_shell,
        "schema": {
            "type": "function",
            "function": {
                "name": "run_shell",
                "description": "Execute a shell command (e.g., git, pytest, ls). Operations are scoped to the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command to execute."}
                    },
                    "required": ["command"]
                }
            }
        }
    }
]
