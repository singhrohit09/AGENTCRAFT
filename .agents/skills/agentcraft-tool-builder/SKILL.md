---
name: agentcraft-tool-builder
description: >-
  Use this skill when authoring, registering, sandboxing, and testing new tools for the AgentCraft AI agent engine.
---

# AgentCraft Tool Builder Skill

This skill guides engineers and agents in developing robust, verifiable tools conforming to the AgentCraft Tool Architecture.

## Authoring Guidelines

### 1. Inherit from `BaseTool`
All tools must subclass `BaseTool` in `ai/tools/base.py`:

```python
from ai.tools.base import BaseTool, ToolParameter
from typing import Any, Dict

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Brief, unambiguous explanation of tool capability.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search or action query.",
                    required=True,
                )
            ]
        )

    def execute(self, query: str) -> Dict[str, Any]:
        # Implement deterministic logic here
        return {"result": f"Processed {query}"}
```

### 2. Register Tool in `ToolRegistry`
Add the new tool to `ai/tools/__init__.py`:

```python
from ai.tools.custom_tool import CustomTool
self.register(CustomTool())
```

### 3. Implement Verification Rules
Ensure tools provide verifiable output structures that can be audited by `VerifierTool`.

### 4. Write Unit Tests
Always add corresponding test cases in `ai/tests/test_tools.py` covering:
- Happy-path execution
- Missing or invalid arguments
- Exception safety
