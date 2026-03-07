import os
import time
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import litellm
except ImportError:
    litellm = None

# Rate Limiter for Gemini (15 requests per minute)
class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.period = 60.0
        self.max_calls = calls_per_minute
        self.timestamps = []
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = time.time()
            # Filter out timestamps older than the period
            self.timestamps = [t for t in self.timestamps if now - t < self.period]
            
            if len(self.timestamps) >= self.max_calls:
                # Calculate wait time based on the oldest timestamp in the window
                wait_time = self.period - (now - self.timestamps[0])
                if wait_time > 0:
                    # Add a small buffer to ensure we are strictly outside the window
                    await asyncio.sleep(wait_time + 0.1)
                    # Refresh time after sleep
                    now = time.time()
                    self.timestamps = [t for t in self.timestamps if now - t < self.period]

            self.timestamps.append(time.time())

# Singleton instance for Gemini Rate Limiting
gemini_limiter = RateLimiter(calls_per_minute=15)

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Defines the interface for generating completions.
    """
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None, 
        **kwargs
    ) -> Any:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dictionaries (role, content).
            tools: Optional list of tool definitions.
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            The LLM response object (compatible with OpenAI/LiteLLM response structure).
        """
        pass

class LiteLLMProvider(LLMProvider):
    """
    Provider implementation using LiteLLM to support multiple backends 
    (OpenAI, Anthropic, Google, etc.) via a unified API.
    """
    
    def __init__(self, model: str = "gpt-4-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        # Check if this is a Gemini model to apply rate limiting
        self.is_gemini = "gemini" in model.lower()

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None, 
        **kwargs
    ) -> Any:
        if not litellm:
            raise ImportError("LiteLLM is not installed. Please install it to use LiteLLMProvider.")
        
        # Apply rate limiting for Gemini models
        if self.is_gemini:
            await gemini_limiter.wait()

        # Prepare arguments, filtering out None values
        call_args = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            **kwargs
        }
        
        if self.api_key:
            call_args["api_key"] = self.api_key
            
        # Remove keys with None values to let defaults take over
        call_args = {k: v for k, v in call_args.items() if v is not None}

        return await litellm.acompletion(**call_args)

class ColabTestProvider(LLMProvider):
    """
    A specialized provider for testing in Google Colab environments.
    It attempts to use the free tier of Gemini (via google.colab.userdata) 
    or falls back to a mock response if no credentials are found.
    """
    
    def __init__(self):
        # Default to a lightweight Gemini model often available in Colab free tier
        self.model = "gemini/gemini-1.5-flash"
        self.api_key = self._resolve_api_key()

    def _resolve_api_key(self) -> Optional[str]:
        """Attempt to retrieve API key from env or Colab userdata."""
        # 1. Check Environment Variable
        key = os.environ.get("GOOGLE_API_KEY")
        if key:
            return key
            
        # 2. Check Google Colab Userdata
        try:
            from google.colab import userdata  # type: ignore
            return userdata.get('GOOGLE_API_KEY')
        except (ImportError, AttributeError, Exception):
            return None

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None, 
        **kwargs
    ) -> Any:
        # If we have an API key and LiteLLM, try to make a real call
        if self.api_key and litellm:
            try:
                return await litellm.acompletion(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    api_key=self.api_key,
                    **kwargs
                )
            except Exception as e:
                # Log error (print for now) and fall through to mock
                print(f"[ColabTestProvider] API call failed: {e}.")
                raise e

        raise RuntimeError("Mock responses are disabled. Please provide a valid API key.")

    def _mock_response(self, messages: List[Dict[str, str]]) -> Any:
        """Generates a mock response object mimicking the OpenAI structure."""
        last_message = messages[-1].get('content', '') if messages else ""
        mock_content = f"[TEST MODE] I received your message: '{last_message[:30]}...'. This is a mock response."

        # Create a structure compatible with dot notation access (response.choices[0].message.content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.role = "assistant"
                self.tool_calls = None
                self.function_call = None

        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
                self.finish_reason = "stop"

        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
                self.id = "mock-response-id"
                self.model = "colab-test-mock"
                self.usage = {"total_tokens": 0}

        return MockResponse(mock_content)

class LLMFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def get_provider(provider_name: str = "openai", **kwargs) -> LLMProvider:
        """
        Get an LLM provider instance.
        
        Args:
            provider_name: 'openai', 'anthropic', 'google', 'colab_test', or 'custom'.
            **kwargs: Arguments passed to the provider (e.g., model, api_key).
        """
        provider_name = provider_name.lower()
        
        if provider_name == "colab_test":
            return ColabTestProvider()
            
        elif provider_name == "anthropic":
            model = kwargs.get("model", "claude-3-opus-20240229")
            return LiteLLMProvider(model=model, api_key=kwargs.get("api_key"))
            
        elif provider_name == "google":
            api_key = os.getenv("GEMINI_API_KEY")
                
            model = kwargs.get("model", "gemini/gemini-3-flash")
            return LiteLLMProvider(model=model, api_key=api_key)
            
        elif provider_name == "openai":
            model = kwargs.get("model", "gpt-4-turbo")
            return LiteLLMProvider(model=model, api_key=kwargs.get("api_key"))
            
        else:
            # Generic fallback for other providers supported by LiteLLM
            model = kwargs.get("model", provider_name) # Treat provider name as model if unknown
            return LiteLLMProvider(model=model, api_key=kwargs.get("api_key"))