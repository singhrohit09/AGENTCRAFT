"""
AgentCraft Safe Code Runner Tool
Executes dynamic Python code blocks within a managed local execution scope,
capturing stdout/stderr, variables, and exceptions with execution timing.
"""

import sys
import io
import math
import json
import re
import datetime
import collections
import statistics
import traceback
from typing import Any, Dict, Optional
from ai.tools.base import BaseTool, ToolParameter


class CodeRunnerTool(BaseTool):
    """Executes Python code blocks safely with captured output and variable inspection."""

    def __init__(self):
        super().__init__(
            name="code_runner",
            description="Executes a Python code block and returns stdout, stderr, and exported variables.",
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="The Python code string to execute.",
                    required=True,
                ),
                ToolParameter(
                    name="context_vars",
                    type="object",
                    description="Optional dictionary of variables to inject into the execution scope.",
                    required=False,
                    default={},
                ),
            ],
        )

    def execute(self, code: str, context_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context_vars = context_vars or {}

        # Safe pre-imported modules available to the script
        execution_scope: Dict[str, Any] = {
            "math": math,
            "json": json,
            "re": re,
            "datetime": datetime,
            "collections": collections,
            "statistics": statistics,
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "min": min,
                "max": max,
                "sum": sum,
                "sorted": sorted,
                "abs": abs,
                "round": round,
                "enumerate": enumerate,
                "zip": zip,
                "filter": filter,
                "map": map,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "ZeroDivisionError": ZeroDivisionError,
            },
        }

        # Inject user variables
        execution_scope.update(context_vars)

        # Redirect standard output and error
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Compile and execute
            compiled_code = compile(code, "<agent_script>", "exec")
            exec(compiled_code, execution_scope)

            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()

            # Filter exported variables (exclude private and built-in modules)
            exported_vars: Dict[str, Any] = {}
            for k, v in execution_scope.items():
                if k.startswith("_") or k in {"math", "json", "re", "datetime", "collections", "statistics"}:
                    continue
                # JSON-serializable representation of result
                try:
                    json.dumps(v)
                    exported_vars[k] = v
                except (TypeError, OverflowError):
                    exported_vars[k] = str(v)

            return {
                "stdout": stdout_text.strip(),
                "stderr": stderr_text.strip(),
                "variables": exported_vars,
                "status": "completed",
            }

        except Exception as e:
            tb_lines = traceback.format_exc().splitlines()
            # Filter traceback to highlight user code
            relevant_tb = "\n".join(tb_lines[-4:])
            raise RuntimeError(f"Code execution failed: {str(e)}\n{relevant_tb}")

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
