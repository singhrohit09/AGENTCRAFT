"""
AgentCraft File Manager Tool
Provides sandboxed, path-traversal-protected filesystem operations
for reading, writing, inspecting, and searching files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from ai.tools.base import BaseTool, ToolParameter


class FileManagerTool(BaseTool):
    """Safely manages files within a designated workspace or sandbox directory."""

    base_dir: Path

    def __init__(self, base_dir: Optional[str] = None):
        super().__init__(
            name="file_manager",
            description="Performs safe file operations (read, write, list, grep, exists, delete) within the sandbox.",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="The file operation to perform: 'read', 'write', 'list', 'exists', 'grep', 'delete'.",
                    required=True,
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path of the target file or directory.",
                    required=True,
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write when action is 'write'.",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Regex or substring pattern to search for when action is 'grep'.",
                    required=False,
                    default="",
                ),
            ],
        )
        self.base_dir = Path(base_dir or "./temp_sandbox").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolves path and enforces that it does not escape base_dir."""
        # Clean relative path
        norm = os.path.normpath(relative_path).lstrip("/\\")
        target = (self.base_dir / norm).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise PermissionError(f"Access denied: Path '{relative_path}' traverses outside sandbox root.")
        return target

    def execute(
        self,
        action: str,
        path: str,
        content: str = "",
        pattern: str = "",
    ) -> Dict[str, Any]:
        target_path = self._resolve_safe_path(path)

        if action == "write":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            return {
                "action": "write",
                "path": str(target_path.relative_to(self.base_dir)),
                "bytes_written": len(content.encode("utf-8")),
                "status": "success",
            }

        elif action == "read":
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: '{path}'")
            if not target_path.is_file():
                raise IsADirectoryError(f"Target '{path}' is a directory, not a file.")
            text = target_path.read_text(encoding="utf-8", errors="replace")
            return {
                "action": "read",
                "path": str(target_path.relative_to(self.base_dir)),
                "content": text,
                "lines": len(text.splitlines()),
                "status": "success",
            }

        elif action == "exists":
            return {
                "action": "exists",
                "path": str(target_path.relative_to(self.base_dir)),
                "exists": target_path.exists(),
                "is_file": target_path.is_file() if target_path.exists() else False,
                "is_dir": target_path.is_dir() if target_path.exists() else False,
            }

        elif action == "list":
            if not target_path.exists():
                raise FileNotFoundError(f"Directory not found: '{path}'")
            if not target_path.is_dir():
                raise NotADirectoryError(f"Target '{path}' is not a directory.")
            entries: List[Dict[str, Any]] = []
            for item in target_path.iterdir():
                entries.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else 0,
                })
            return {
                "action": "list",
                "path": str(target_path.relative_to(self.base_dir)),
                "entries": entries,
                "total_items": len(entries),
            }

        elif action == "grep":
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: '{path}'")
            lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines()
            matches = []
            for idx, line in enumerate(lines, 1):
                if pattern.lower() in line.lower():
                    matches.append({"line_number": idx, "content": line})
            return {
                "action": "grep",
                "path": str(target_path.relative_to(self.base_dir)),
                "pattern": pattern,
                "matches": matches,
                "match_count": len(matches),
            }

        elif action == "delete":
            if not target_path.exists():
                return {"action": "delete", "path": path, "deleted": False, "reason": "Not found"}
            if target_path.is_file():
                target_path.unlink()
            elif target_path.is_dir():
                import shutil
                shutil.rmtree(target_path)
            return {"action": "delete", "path": path, "deleted": True}

        else:
            raise ValueError(f"Unknown file action: '{action}'. Expected: read, write, list, exists, grep, delete.")
