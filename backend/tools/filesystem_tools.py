import os
import shutil
from pathlib import Path
from typing import List, Union, Dict, Any

def read_file(file_path: str) -> str:
    """Read the contents of a file. Use this to examine logs, reports, or research data."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """Create or overwrite a file with specific content. Use this to save research reports or data summaries."""
    try:
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{file_path}' written successfully."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(directory_path: str = ".") -> str:
    """List the contents of a directory. Use this to explore the project structure or find saved reports."""
    try:
        items = os.listdir(directory_path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def create_directory(directory_path: str) -> str:
    """Create a new directory (and any parent directories). Use this to organize research results."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Directory '{directory_path}' created successfully."
    except Exception as e:
        return f"Error creating directory: {str(e)}"

def delete_path(path: str) -> str:
    """Delete a file or directory. Use with caution."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"File '{path}' deleted."
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Directory '{path}' deleted."
        else:
            return f"Error: '{path}' does not exist."
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
                        "file_path": {"type": "string", "description": "Absolute or relative path to the file."}
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
                        "file_path": {"type": "string", "description": "Path to the file to create/overwrite."},
                        "content": {"type": "string", "description": "The text content to write."}
                    },
                    "required": ["file_path", "content"]
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
                        "directory_path": {"type": "string", "description": "Path to list (default is current directory).", "default": "."}
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
                        "directory_path": {"type": "string", "description": "Path of the directory to create."}
                    },
                    "required": ["directory_path"]
                }
            }
        }
    }
]
