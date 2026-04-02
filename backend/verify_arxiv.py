import asyncio
import sys
import os

# Add parent directory to sys.path to import agent_reach_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_reach_tools import arxiv_search

async def main():
    print("--- Testing ArXiv Search Tool ---")
    
    query = "Transformer Large Language Models"
    print(f"Querying ArXiv for: '{query}'...")
    
    result = await arxiv_search(query, limit=3)
    
    print("\nSearch Results:")
    print("-" * 20)
    print(result)
    print("-" * 20)
    
    if "### [" in result and "**Authors**:" in result:
        print("\nSUCCESS: ArXiv search returned formatted results.")
    else:
        print("\nFAILURE: ArXiv search result format unrecognized or empty.")

if __name__ == "__main__":
    asyncio.run(main())
