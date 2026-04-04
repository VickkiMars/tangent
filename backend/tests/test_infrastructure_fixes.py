import os
import pytest
from pathlib import Path
from tools.shell_tools import run_shell
from tools.filesystem_tools import read_file, write_file, patch_file, list_directory, create_directory

# Setup a temporary workspace for testing
TEST_WORKSPACE = Path("/tmp/agent_test_workspace")
TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
os.environ["AGENT_WORKSPACE"] = str(TEST_WORKSPACE)

def test_shell_tool_basic():
    output = run_shell("echo hello")
    assert "hello" in output

def test_shell_tool_forbidden():
    output = run_shell("rm -rf /")
    assert "Error: Command 'rm -rf /' contains forbidden sequence 'rm -rf /'" in output

def test_filesystem_sandbox_enforcement():
    # Try to write outside workspace
    output = write_file("/tmp/evil.txt", "evil")
    assert "Access denied" in output
    assert not os.path.exists("/tmp/evil.txt")

def test_filesystem_basic_ops():
    # Write
    res = write_file("test.txt", "hello world")
    assert "written successfully" in res
    assert (TEST_WORKSPACE / "test.txt").exists()
    
    # Read
    content = read_file("test.txt")
    assert content == "hello world"
    
    # List
    items = list_directory(".")
    assert "test.txt" in items
    
    # Patch
    res = patch_file("test.txt", "world", "tangent")
    assert "patched successfully" in res
    assert read_file("test.txt") == "hello tangent"

def test_create_directory():
    res = create_directory("subdir/nested")
    assert "created successfully" in res
    assert (TEST_WORKSPACE / "subdir/nested").is_dir()

def test_patch_file_not_found():
    res = patch_file("test.txt", "nonexistent", "foo")
    assert "Error: Target text not found" in res

if __name__ == "__main__":
    # Simple manual run if pytest is not available
    print("Running manual verification...")
    try:
        test_shell_tool_basic()
        print("test_shell_tool_basic: PASS")
        test_shell_tool_forbidden()
        print("test_shell_tool_forbidden: PASS")
        test_filesystem_sandbox_enforcement()
        print("test_filesystem_sandbox_enforcement: PASS")
        test_filesystem_basic_ops()
        print("test_filesystem_basic_ops: PASS")
        test_create_directory()
        print("test_create_directory: PASS")
        test_patch_file_not_found()
        print("test_patch_file_not_found: PASS")
        print("\nAll infrastructure tests PASSED.")
    except Exception as e:
        print(f"\nTests FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
