import sys
import os
from pathlib import Path

# Add backend to sys.path
sys.path.append("/home/kami/Desktop/codebase/tangent/backend")

from tools.agent_reach_tools import AGENT_REACH_TOOLS

def verify_registration():
    tool_names = [t["name"] for t in AGENT_REACH_TOOLS]
    print(f"Registered tools: {tool_names}")
    
    if "web_search_batch" in tool_names:
        print("SUCCESS: web_search_batch is registered.")
        # Find the tool info
        tool = next(t for t in AGENT_REACH_TOOLS if t["name"] == "web_search_batch")
        assert callable(tool["func"])
        print("SUCCESS: web_search_batch function is callable.")
    else:
        print("FAILURE: web_search_batch is NOT registered.")
        sys.exit(1)

if __name__ == "__main__":
    verify_registration()
