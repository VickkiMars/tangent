import asyncio
import sys
import os

# Add parent directory to sys.path to import agent_reach_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_reach_tools import wikipedia_search, wikipedia_read

async def main():
    print("--- Testing Wikipedia Search & Read ---")
    
    # 1. Search
    query = "Artificial Intelligence"
    print(f"Searching Wikipedia for: '{query}'...")
    search_results = await wikipedia_search(query, limit=3)
    print("\nSearch Results:")
    print(search_results)
    
    # 2. Read
    if "Artificial intelligence" in search_results:
        title = "Artificial intelligence"
    else:
        # Fallback to first line if format is different
        title = search_results.split("\n")[0].split("]")[0][3:] if search_results.startswith("- [") else "Artificial intelligence"
        
    print(f"\nReading Wikipedia page: '{title}'...")
    content = await wikipedia_read(title)
    
    print("\nPage Content (first 500 chars):")
    print("-" * 20)
    print(content[:500] + "...")
    print("-" * 20)
    
    if len(content) > 100:
        print("\nSUCCESS: Wikipedia tools are working.")
    else:
        print("\nFAILURE: Wikipedia content unexpectedly short or empty.")

if __name__ == "__main__":
    asyncio.run(main())
