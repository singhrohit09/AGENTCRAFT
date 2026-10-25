"""
AgentCraft Tools Registry & Factory
"""

from typing import Dict, List, Optional
from ai.tools.base import BaseTool, ToolResult, ToolParameter
from ai.tools.code_runner import CodeRunnerTool
from ai.tools.file_manager import FileManagerTool
from ai.tools.data_analyzer import DataAnalyzerTool
from ai.tools.web_fetcher import WebFetcherTool
from ai.tools.verifier import VerifierTool


class ToolRegistry:
    """Central registry and dispatcher for AgentCraft tools."""

    def __init__(self, sandbox_dir: Optional[str] = None, allow_network: bool = True):
        self._tools: Dict[str, BaseTool] = {}
        # Register standard built-in tools
        self.register(CodeRunnerTool())
        self.register(FileManagerTool(base_dir=sandbox_dir))
        self.register(DataAnalyzerTool())
        self.register(WebFetcherTool(allow_network=allow_network))
        self.register(VerifierTool())

    def register(self, tool: BaseTool) -> None:
        """Registers a tool instance into the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieves a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        """Returns metadata and parameter schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Executes a tool by name with provided keyword arguments."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found in registry. Registered tools: {list(self._tools.keys())}",
                tool_name=tool_name,
            )
        return tool.run(**kwargs)


__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "ToolRegistry",
    "CodeRunnerTool",
    "FileManagerTool",
    "DataAnalyzerTool",
    "WebFetcherTool",
    "VerifierTool",
]
