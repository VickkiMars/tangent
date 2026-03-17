import requests

def search_searxng(query):
    url = "https://searx.be/search"
    
    params = {
        "q": query,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        
        for i, result in enumerate(results[:5], start=1):
            print(f"{i}. {result.get('title')}")
            print(f"   {result.get('url')}\n")

    except requests.exceptions.RequestException as e:
        print("Error:", e)


if __name__ == "__main__":
    query = input("Enter search query: ")
    search_searxng(query)
