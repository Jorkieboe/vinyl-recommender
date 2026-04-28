import json
import inspect
from typing import Any, Callable, Dict, List, Optional, Type
from datetime import datetime
from pydantic import create_model, Field
from core.logger import console
import os
import pathspec
from enum import Enum


class Tool:
    def __init__(self, fn: Callable, name: str, description: str, parameters_model: Type, requires_approval: bool = False):
        self.fn = fn
        self.name = name
        self.description = description
        self.parameters_model = parameters_model
        self.requires_approval = requires_approval

    def get_schema(self) -> Dict[str, Any]:
        """Returns the OpenAI-style tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_model.model_json_schema()
            }
        }

    async def execute(self, **kwargs) -> Any:
        try:
            validated_params = self.parameters_model(**kwargs)
   
            params_dict = validated_params.model_dump()

            if inspect.iscoroutinefunction(self.fn):
                return await self.fn(**params_dict)
            return self.fn(**params_dict)
        except Exception as e:
            return f"Error: {str(e)}"

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, fn: Callable):
        name = fn.__name__
        doc = inspect.getdoc(fn) or "No description provided."
        # Check if function was marked by @requires_approval decorator
        needs_approval = getattr(fn, "_requires_approval", False)

        # Extract parameters for Pydantic model
        sig = inspect.signature(fn)
        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self": continue

            # Default to Any if no type hint
            annotation = param.annotation if param.annotation != inspect.Parameter.empty else Any
            # Handle defaults
            default = param.default if param.default != inspect.Parameter.empty else ...

            fields[param_name] = (annotation, default)

        # Dynamically create a Pydantic model for parameter validation
        model = create_model(f"{name}_params", **fields)

        self.tools[name] = Tool(fn, name, doc, model, requires_approval=needs_approval)
        return fn

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self.tools.values()]

# Global registry instance
registry = ToolRegistry()

def tool(fn: Callable):
    """Decorator to register a tool."""
    return registry.register(fn)

def requires_approval(fn: Callable):
    """Decorator to mark a tool as requiring human approval before execution."""
    fn._requires_approval = True
    return fn

# --- Core Lab Tools ---

@tool
def get_time():
    """Returns the current system time. Useful for temporal reasoning."""
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")

