import asyncio
import sys
import os

# Add parent directory to sys.path to import agent_reach_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_reach_tools import reddit_search, reddit_read

async def main():
    print("--- Testing Reddit Search & Read ---")
    
    # 1. Search
    query = "Large Language Models"
    print(f"Searching Reddit for: '{query}'...")
    search_results = await reddit_search(query, limit=3)
    print("\nSearch Results:")
    print(search_results)
    
    # Extract the first URL for testing reddit_read
    if "https://www.reddit.com" in search_results:
        import re
        urls = re.findall(r'(https?://www.reddit.com/r/[\w/]+)', search_results)
        if urls:
            test_url = urls[0]
            print(f"\nReading Reddit post: '{test_url}'...")
            content = await reddit_read(test_url)
            
            print("\nPost Content & Top Comments (first 1000 chars):")
            print("-" * 20)
            print(content[:1000] + "...")
            print("-" * 20)
            
            if len(content) > 100:
                print("\nSUCCESS: Reddit tools are working.")
            else:
                print("\nFAILURE: Reddit content unexpectedly short or empty.")
        else:
            print("\nFAILURE: Could not extract URL from search results.")
    else:
        print("\nFAILURE: No Reddit results found.")

if __name__ == "__main__":
    asyncio.run(main())
