import os
import shutil
from pathlib import Path
from typing import List, Union, Dict, Any

def _get_workspace_path() -> Path:
    """Return the absolute path of the AGENT_WORKSPACE, defaulting to current directory."""
    workspace = os.getenv("AGENT_WORKSPACE", os.getcwd())
    return Path(workspace).resolve()

def _validate_path(path_str: str, must_exist: bool = False) -> Path:
    """Ensure the path is within the AGENT_WORKSPACE and return the resolved Path object."""
    workspace = _get_workspace_path()
    # Resolve the path relative to the workspace
    target = (workspace / path_str).resolve()
    
    # Check if the target path is within the workspace
    if not str(target).startswith(str(workspace)):
        raise PermissionError(f"Access denied: path '{path_str}' is outside the workspace '{workspace}'.")
    
    if must_exist and not target.exists():
        raise FileNotFoundError(f"Path '{path_str}' does not exist.")
        
    return target

def read_file(file_path: str) -> str:
    """Read the contents of a file. Use this to examine logs, reports, or research data."""
    try:
        path = _validate_path(file_path, must_exist=True)
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """Create or overwrite a file with specific content. Use this to save research reports or data summaries."""
    try:
        path = _validate_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"File '{file_path}' written successfully."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def patch_file(file_path: str, target: str, replacement: str) -> str:
    """Surgically replace a specific string or block of text in a file. Use this for small code edits."""
    try:
        path = _validate_path(file_path, must_exist=True)
        content = path.read_text(encoding="utf-8")
        if target not in content:
            return f"Error: Target text not found in '{file_path}'."
        
        new_content = content.replace(target, replacement)
        path.write_text(new_content, encoding="utf-8")
        return f"File '{file_path}' patched successfully."
    except Exception as e:
        return f"Error patching file: {str(e)}"

def list_directory(directory_path: str = ".") -> str:
    """List the contents of a directory. Use this to explore the project structure or find saved reports."""
    try:
        path = _validate_path(directory_path, must_exist=True)
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def create_directory(directory_path: str) -> str:
    """Create a new directory (and any parent directories). Use this to organize research results."""
    try:
        path = _validate_path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return f"Directory '{directory_path}' created successfully."
    except Exception as e:
        return f"Error creating directory: {str(e)}"

def delete_path(path_str: str) -> str:
    """Delete a file or directory. Use with caution."""
    try:
        path = _validate_path(path_str, must_exist=True)
        if path.is_file():
            path.unlink()
            return f"File '{path_str}' deleted."
        elif path.is_dir():
            shutil.rmtree(path)
            return f"Directory '{path_str}' deleted."
        else:
            return f"Error: '{path_str}' is neither a file nor a directory."
    except Exception as e:
        return f"Error deleting path: {str(e)}"

FILESYSTEM_TOOLS = [
    {
        "name": "read_file",
        "func": read_file,
        "schema": {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a text file from the local filesystem.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file relative to the workspace."}
                    },
                    "required": ["file_path"]
                }
            }
        }
    },
    {
        "name": "write_file",
        "func": write_file,
        "schema": {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create a new file or overwrite an existing one with text content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file relative to the workspace."},
                        "content": {"type": "string", "description": "The text content to write."}
                    },
                    "required": ["file_path", "content"]
                }
            }
        }
    },
    {
        "name": "patch_file",
        "func": patch_file,
        "schema": {
            "type": "function",
            "function": {
                "name": "patch_file",
                "description": "Replace a specific string or block of code in a file. Use for small, surgical edits.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file relative to the workspace."},
                        "target": {"type": "string", "description": "The exact text to find and replace."},
                        "replacement": {"type": "string", "description": "The new text to insert."}
                    },
                    "required": ["file_path", "target", "replacement"]
                }
            }
        }
    },
    {
        "name": "list_directory",
        "func": list_directory,
        "schema": {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List all files and subdirectories in a given path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "description": "Path to list (default is workspace root).", "default": "."}
                    }
                }
            }
        }
    },
    {
        "name": "create_directory",
        "func": create_directory,
        "schema": {
            "type": "function",
            "function": {
                "name": "create_directory",
                "description": "Create a new directory recursively.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "description": "Path of the directory relative to the workspace."}
                    },
                    "required": ["directory_path"]
                }
            }
        }
    }
]
