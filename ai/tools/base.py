"""
AgentCraft Tool Base Architecture
Defines the abstract interface, input schema definitions, and execution results
for all tools in the AgentCraft reasoning system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time


class ToolParameter(BaseModel):
    """Schema descriptor for tool arguments."""
    name: str
    type: str  # "string" | "integer" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolResult(BaseModel):
    """Encapsulates the output of a tool execution with telemetry and audit metadata."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_name: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "tool_name": self.tool_name,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """Abstract base class that all AgentCraft tools must inherit from."""

    name: str
    description: str
    parameters: List[ToolParameter]

    def __init__(self, name: str, description: str, parameters: Optional[List[ToolParameter]] = None):
        self.name = name
        self.description = description
        self.parameters = parameters or []

    def get_schema(self) -> Dict[str, Any]:
        """Returns JSON schema representation of the tool."""
        properties = {}
        required = []
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def validate_inputs(self, kwargs: Dict[str, Any]) -> Optional[str]:
        """Validates that all required parameters are present."""
        for param in self.parameters:
            if param.required and param.name not in kwargs and param.default is None:
                return f"Missing required parameter: '{param.name}'"
        return None

    def run(self, **kwargs: Any) -> ToolResult:
        """Executes the tool with timing, validation, and error wrapping."""
        validation_error = self.validate_inputs(kwargs)
        if validation_error:
            return ToolResult(
                success=False,
                error=validation_error,
                tool_name=self.name,
                metadata={"validation_failed": True},
            )

        start_time = time.perf_counter()
        try:
            output = self.execute(**kwargs)
            duration = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=output,
                execution_time_ms=duration,
                tool_name=self.name,
            )
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                execution_time_ms=duration,
                tool_name=self.name,
            )

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Concrete execution logic implemented by subclasses."""
        pass
