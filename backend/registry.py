import logging
import inspect
from functools import wraps
from typing import Callable, Dict, Any, List, Union

logger = logging.getLogger(__name__)

class ToolAdapter:
    def get_tools(self) -> Dict[str, Callable]:
        raise NotImplementedError
        
    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError

class GlobalToolRegistry:
    def __init__(self):
        self._registry: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._adapters: List[ToolAdapter] = []

    def register(self, name: str, func: Callable, schema: Dict[str, Any]):
        """Stores the function pointer and its JSON Schema definition."""
        self._registry[name] = func
        self._schemas[name] = schema
        
    def register_adapter(self, adapter: ToolAdapter):
        """Registers a tool adapter (e.g., Composio, LangChain)"""
        self._adapters.append(adapter)
        
        tools = adapter.get_tools()
        schemas = adapter.get_schemas()
        
        for name, func in tools.items():
            if name in schemas:
                self.register(name, func, schemas[name])

    def _wrap_with_audit(self, name: str, func: Callable) -> Callable:
        """Wraps a tool execution with auditing/logging. Handles both sync and async tools."""
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger.info(f"[AUDIT] Executing tool: '{name}' | Args: {args} | Kwargs: {kwargs}")
                try:
                    result = await func(*args, **kwargs)
                    logger.info(f"[AUDIT] Tool success: '{name}' | Result preview: {str(result)[:200]}")
                    return result
                except Exception as e:
                    logger.error(f"[AUDIT] Tool failed: '{name}' | Error: {str(e)}")
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.info(f"[AUDIT] Executing tool: '{name}' | Args: {args} | Kwargs: {kwargs}")
                try:
                    result = func(*args, **kwargs)
                    logger.info(f"[AUDIT] Tool success: '{name}' | Result preview: {str(result)[:200]}")
                    return result
                except Exception as e:
                    logger.error(f"[AUDIT] Tool failed: '{name}' | Error: {str(e)}")
                    raise
            return wrapper

    def get_ephemeral_toolkit(self, allowed_tools: list[str]) -> Dict[str, Callable]:
        """Returns a tightly scoped dictionary of only the permitted functions."""
        restricted_toolkit = {}
        for tool_name in allowed_tools:
            if tool_name not in self._registry:
                raise ValueError(f"Security Fault: Blueprint requested unknown tool '{tool_name}'")
            restricted_toolkit[tool_name] = self._wrap_with_audit(tool_name, self._registry[tool_name])
        return restricted_toolkit
        
    def get_ephemeral_schemas(self, allowed_tools: list[str]) -> list[Dict[str, Any]]:
        """Returns only the schemas for the LLM prompt."""
        return [self._schemas[name] for name in allowed_tools if name in self._schemas]