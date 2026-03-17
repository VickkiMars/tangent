from typing import Callable, Dict, Any, List

# ToolAdapter is the canonical base class defined in registry.py.
# Importing from there avoids having two independent definitions.
from registry import ToolAdapter


class LangchainAdapter(ToolAdapter):
    def __init__(self, tools: List[Any]):
        """Accepts a list of LangChain tools"""
        self.lc_tools = tools

    def get_tools(self) -> Dict[str, Callable]:
        tools_dict = {}
        for tool in self.lc_tools:
            # Wrap LangChain tool invocation
            def _run_tool(tool_inst=tool, **kwargs):
                return tool_inst.invoke(kwargs)
            tools_dict[tool.name] = _run_tool
        return tools_dict

    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        schemas_dict = {}
        for tool in self.lc_tools:
            try:
                # Prefer the newer API (langchain-core 0.2+)
                from langchain_core.utils.function_calling import convert_to_openai_tool
                schemas_dict[tool.name] = convert_to_openai_tool(tool)
            except (ImportError, Exception):
                try:
                    from langchain_core.utils.function_calling import format_tool_to_openai_function
                    func_schema = format_tool_to_openai_function(tool)
                    schemas_dict[tool.name] = {"type": "function", "function": func_schema}
                except (ImportError, Exception):
                    # Fallback: build a minimal schema from the tool's args_schema
                    try:
                        input_schema = tool.args_schema.schema() if tool.args_schema else {"properties": {}, "type": "object"}
                        schemas_dict[tool.name] = {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": getattr(tool, "description", ""),
                                "parameters": input_schema,
                            }
                        }
                    except Exception:
                        pass
        return schemas_dict


class ComposioAdapter(ToolAdapter):
    def __init__(self, toolset: Any, actions: List[Any] = None, apps: List[Any] = None):
        """Accepts a ComposioToolSet (composio_openai) instance and actions/apps to load"""
        self.toolset = toolset
        self.actions = actions
        self.apps = apps
        self._openai_tools = []
        if self.actions:
            self._openai_tools.extend(self.toolset.get_tools(actions=self.actions))
        if self.apps:
            self._openai_tools.extend(self.toolset.get_tools(apps=self.apps))

    def get_tools(self) -> Dict[str, Callable]:
        tools_dict = {}
        for tool in self._openai_tools:
            tool_name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
            if not tool_name:
                continue

            def _run_tool(action_name=tool_name, **kwargs):
                return self.toolset.execute_action(action=action_name, params=kwargs)

            tools_dict[tool_name] = _run_tool
        return tools_dict

    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        schemas_dict = {}
        for tool in self._openai_tools:
            if 'function' in tool:
                # Tool is already in full OpenAI format {"type": "function", "function": {...}}.
                # Store the whole object so the API receives the correct shape.
                schemas_dict[tool['function']['name']] = tool
            else:
                # Bare function dict — wrap it.
                tool_name = tool.get('name', '')
                schemas_dict[tool_name] = {"type": "function", "function": tool}
        return schemas_dict
