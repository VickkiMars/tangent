import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.dirname(__file__))

from engine.meta import MetaAgent
from tools.agent_reach_tools import AGENT_REACH_TOOLS
from tools.registry import GlobalToolRegistry

async def verify_research_flow():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    print("--- Tangent Research Flow Verification ---")
    
    # 1. Initialize Registry and register tools
    print("[*] Initializing GlobalToolRegistry...")
    registry = GlobalToolRegistry()
    for tool_info in AGENT_REACH_TOOLS:
        registry.register(tool_info["name"], tool_info["func"], tool_info["schema"])
    
    available_tools = list(registry._registry.keys())
    tool_descriptions = {name: schema.get("function", {}).get("description", "") 
                        for name, schema in registry._schemas.items()}
    
    print(f"[*] Registered {len(available_tools)} tools.")
    assert "web_search" in available_tools
    assert "web_search_batch" in available_tools
    print("✅ Tool registration confirmed.")

    # 2. Architect Workflow with MetaAgent
    print("[*] Asking MetaAgent to architect a research workflow...")
    # Using gemini-flash-lite-latest for speed/cost and availability
    meta_agent = MetaAgent(model_name="gemini/gemini-flash-lite-latest")
    objective = "Provide a detailed analysis of the current state of consumer AI search engines like Perplexity, SearchGPT, and Exa."
    
    try:
        manifest = await asyncio.to_thread(
            meta_agent.architect_workflow, 
            objective, 
            available_tools, 
            tool_descriptions
        )
        
        print(f"[*] MetaAgent generated {len(manifest.blueprints)} blueprints.")
        
        research_agents = [b for b in manifest.blueprints if "web_search_batch" in b.injected_tools]
        
        if research_agents:
            print(f"✅ Found {len(research_agents)} research agents assigned with 'web_search_batch'.")
            for agent in research_agents:
                print(f"   - Agent ID: {agent.agent_id}")
                print(f"   - Injected Tools: {agent.injected_tools}")
        else:
            print("❌ Error: No agents were assigned 'web_search_batch'.")
            
        deprecated_tool_usage = [b for b in manifest.blueprints if "web_search" in b.injected_tools]
        if deprecated_tool_usage:
            print("⚠️ Warning: MetaAgent used 'web_search' (deprecated) instead of 'web_search_batch'.")
        else:
            print("✅ MetaAgent correctly avoided the deprecated 'web_search' tool.")

    except Exception as e:
        print(f"❌ Error during workflow architecting: {e}")

if __name__ == "__main__":
    asyncio.run(verify_research_flow())
