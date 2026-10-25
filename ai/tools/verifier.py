"""
AgentCraft Verifier Tool
Evaluates acceptance criteria, assertion rules, schema consistency,
and output boundaries to prevent hallucinated results and silent failures.
"""

from typing import Any, Dict, List, Optional
import re
from ai.tools.base import BaseTool, ToolParameter


class VerifierTool(BaseTool):
    """Evaluates result assertions and validation contracts against tool outputs or session variables."""

    def __init__(self):
        super().__init__(
            name="verifier",
            description="Evaluates verification assertions (thresholds, schemas, regex, non-empty, expressions) on step outputs.",
            parameters=[
                ToolParameter(
                    name="assertions",
                    type="array",
                    description="List of assertion rule objects to evaluate.",
                    required=True,
                ),
                ToolParameter(
                    name="subject",
                    type="object",
                    description="The subject data or context dictionary to test against.",
                    required=True,
                ),
            ],
        )

    def execute(self, assertions: List[Dict[str, Any]], subject: Any) -> Dict[str, Any]:
        results = []
        all_passed = True

        for idx, rule in enumerate(assertions):
            rule_type = rule.get("type", "non_empty")
            target_key = rule.get("key")
            description = rule.get("description", f"Assertion #{idx + 1} ({rule_type})")

            # Extract value
            val = subject
            if target_key:
                if isinstance(subject, dict):
                    val = subject.get(target_key)
                else:
                    val = getattr(subject, target_key, None)

            passed = False
            message = ""

            try:
                if rule_type == "non_empty":
                    if val is not None and len(str(val).strip()) > 0 and val != [] and val != {}:
                        passed = True
                        message = "Value is present and non-empty."
                    else:
                        passed = False
                        message = f"Value for '{target_key or 'subject'}' is empty or null."

                elif rule_type == "threshold":
                    op = rule.get("operator", ">=")
                    threshold = float(rule.get("value", 0))
                    num_val = float(val) if val is not None else 0.0

                    if op == ">=":
                        passed = num_val >= threshold
                    elif op == "<=":
                        passed = num_val <= threshold
                    elif op == ">":
                        passed = num_val > threshold
                    elif op == "<":
                        passed = num_val < threshold
                    elif op == "==":
                        passed = num_val == threshold
                    elif op == "!=":
                        passed = num_val != threshold
                    else:
                        passed = False
                        message = f"Unknown comparison operator: '{op}'"

                    if not message:
                        message = f"Evaluated: {num_val} {op} {threshold} -> {passed}"

                elif rule_type == "regex":
                    pattern = rule.get("pattern", ".*")
                    passed = bool(re.search(pattern, str(val)))
                    message = f"Pattern '{pattern}' match on value: {passed}"

                elif rule_type == "schema":
                    required_keys = rule.get("required_keys", [])
                    if isinstance(val, dict):
                        missing = [k for k in required_keys if k not in val]
                        passed = len(missing) == 0
                        message = "All required schema keys present." if passed else f"Missing required keys: {missing}"
                    else:
                        passed = False
                        message = f"Expected dict for schema check, received {type(val).__name__}"

                elif rule_type == "expression":
                    expr = rule.get("expression", "True")
                    eval_scope = {"data": val, "subject": subject, "len": len, "str": str, "int": int, "float": float}
                    passed = bool(eval(expr, {"__builtins__": {}}, eval_scope))
                    message = f"Expression '{expr}' evaluated to {passed}"

                else:
                    passed = False
                    message = f"Unrecognized rule type: '{rule_type}'"

            except Exception as e:
                passed = False
                message = f"Evaluation error: {str(e)}"

            if not passed:
                all_passed = False

            results.append({
                "assertion_id": idx + 1,
                "description": description,
                "type": rule_type,
                "passed": passed,
                "message": message,
            })

        return {
            "verified": all_passed,
            "total_assertions": len(assertions),
            "passed_count": sum(1 for r in results if r["passed"]),
            "failed_count": sum(1 for r in results if not r["passed"]),
            "details": results,
        }
