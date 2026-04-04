import os
import urllib.request
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in the environment variables.")
    exit(1)

print(f"Testing Gemini API Key: {api_key[:5]}...{api_key[-4:]}")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            models = data.get("models", [])
            print(f"\nSuccessfully authenticated! Found {len(models)} models available to your API key:")
            print("-" * 50)
            
            # Print specifically the text/chat models that are usually relevant
            for model in models:
                name = model.get("name", "")
                version = model.get("version", "N/A")
                display_name = model.get("displayName", "")
                
                # We can filter for only models that support generateContent to keep the list clean
                supported_methods = model.get("supportedGenerationMethods", [])
                if "generateContent" in supported_methods:
                    print(f"- {name} (Version: {version})")
                    # print(f"  Description: {model.get('description', 'N/A')}")
                    
        else:
            print(f"Failed with status code: {response.status}")

except urllib.error.HTTPError as e:
    print(f"\nHTTP Error: {e.code} - {e.reason}")
    try:
        error_info = json.loads(e.read().decode())
        print(json.dumps(error_info, indent=2))
    except:
        pass
except urllib.error.URLError as e:
    print(f"\nConnection Error: {e.reason}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
