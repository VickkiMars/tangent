import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current directory to path so we can import agent_reach_tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_reach_tools import web_search

async def verify_queries():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    
    queries = [
        "Who is the current CEO of Nvidia and what was their total compensation in 2024?",
        "List the top 5 highest grossing movies of all time adjusted for inflation, and their main directors.",
        "What are the latest clinical trial results for Alzheimer's drugs published in 2025/2026?",
        "Compare the price of gold per ounce in USD, EUR, and GBP as of today.",
        "Who won the most recent Men's World Cup and who was the top scorer?",
        "Provide a summary of the latest SpaceX Starship launch attempt results.",
        "What is the current population of Tokyo vs Shanghai in 2026?",
        "List the winners of the 2026 Oscars for Best Picture, Best Actor, and Best Actress.",
        "What are the main technical specifications of the latest iPhone released before March 2026?",
        "Summarize the key takeaways from the most recent COP summit (COP30 or COP31)."
    ]
    
    print("=== SERPER.DEV INTEGRATION VERIFICATION ===\n")
    
    for i, query in enumerate(queries, 1):
        print(f"--- QUERY {i}: {query} ---")
        try:
            result = await web_search(query, num_results=5)
            print(result)
        except Exception as e:
            print(f"FAILED: {str(e)}")
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(verify_queries())
