"""
AgentCraft Data Analyzer Tool
Provides statistical profiling, schema inference, outlier detection,
and aggregation on tabular / JSON datasets without requiring heavy external dependencies.
"""

import math
import statistics
import collections
from typing import Any, Dict, List, Optional, Union
import json
from ai.tools.base import BaseTool, ToolParameter


class DataAnalyzerTool(BaseTool):
    """Analyzes datasets: statistics, schema detection, IQR outlier analysis, and aggregations."""

    def __init__(self):
        super().__init__(
            name="data_analyzer",
            description="Analyzes tabular or structured JSON records: compute statistics, infer schemas, detect outliers, and aggregate.",
            parameters=[
                ToolParameter(
                    name="data",
                    type="array",
                    description="List of records (dictionaries) or JSON string containing a list of records.",
                    required=True,
                ),
                ToolParameter(
                    name="action",
                    type="string",
                    description="Analysis action: 'summarize', 'schema', 'outliers', 'aggregate'.",
                    required=False,
                    default="summarize",
                ),
                ToolParameter(
                    name="target_column",
                    type="string",
                    description="Column to inspect for outliers or aggregation.",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="group_by",
                    type="string",
                    description="Optional column to group by during aggregation.",
                    required=False,
                    default="",
                ),
            ],
        )

    def _normalize_data(self, data: Union[str, List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        if isinstance(data, str):
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ValueError("Data must parse to a list of records.")
        elif isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        raise TypeError("Data must be a list of records or JSON string.")

    def execute(
        self,
        data: Union[str, List[Dict[str, Any]], Dict[str, Any]],
        action: str = "summarize",
        target_column: str = "",
        group_by: str = "",
    ) -> Dict[str, Any]:
        records = self._normalize_data(data)
        if not records:
            return {"total_records": 0, "columns": {}, "message": "Dataset is empty."}

        all_columns = sorted(list({k for r in records for k in r.keys()}))

        if action == "schema":
            column_types: Dict[str, str] = {}
            for col in all_columns:
                types_seen = set()
                for r in records:
                    val = r.get(col)
                    if val is not None:
                        types_seen.add(type(val).__name__)
                column_types[col] = "/".join(sorted(types_seen)) if types_seen else "null"
            return {
                "action": "schema",
                "total_records": len(records),
                "columns": column_types,
            }

        elif action == "outliers":
            if not target_column:
                # pick first numeric column
                for col in all_columns:
                    vals = [r.get(col) for r in records if isinstance(r.get(col), (int, float)) and not isinstance(r.get(col), bool)]
                    if vals:
                        target_column = col
                        break
            if not target_column:
                raise ValueError("No numeric column available for outlier analysis.")

            values = [float(r[target_column]) for r in records if target_column in r and isinstance(r[target_column], (int, float)) and not isinstance(r[target_column], bool)]
            if len(values) < 4:
                return {
                    "action": "outliers",
                    "target_column": target_column,
                    "outliers_found": 0,
                    "outliers": [],
                    "message": "Insufficient numeric sample size (< 4) for IQR computation.",
                }

            sorted_vals = sorted(values)
            n = len(sorted_vals)
            q1 = sorted_vals[int(n * 0.25)]
            q3 = sorted_vals[int(n * 0.75)]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            return {
                "action": "outliers",
                "target_column": target_column,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "outliers_found": len(outliers),
                "outliers": outliers,
            }

        elif action == "aggregate":
            if not target_column:
                raise ValueError("target_column is required for aggregation.")

            if group_by:
                groups: Dict[str, List[float]] = {}
                for r in records:
                    g_val = str(r.get(group_by, "unknown"))
                    val = r.get(target_column)
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        groups.setdefault(g_val, []).append(float(val))
                summary = {}
                for g_val, g_list in groups.items():
                    summary[g_val] = {
                        "count": len(g_list),
                        "sum": sum(g_list),
                        "mean": round(statistics.mean(g_list), 4) if g_list else 0.0,
                    }
                return {"action": "aggregate", "group_by": group_by, "target": target_column, "groups": summary}
            else:
                vals = [float(r[target_column]) for r in records if target_column in r and isinstance(r[target_column], (int, float)) and not isinstance(r[target_column], bool)]
                return {
                    "action": "aggregate",
                    "target": target_column,
                    "count": len(vals),
                    "sum": sum(vals),
                    "mean": round(statistics.mean(vals), 4) if vals else 0.0,
                    "min": min(vals) if vals else None,
                    "max": max(vals) if vals else None,
                }

        # Default action: summarize
        col_summaries: Dict[str, Any] = {}
        for col in all_columns:
            raw_vals = [r.get(col) for r in records]
            non_nulls = [v for v in raw_vals if v is not None]
            null_count = len(raw_vals) - len(non_nulls)
            numeric_vals = [float(v) for v in non_nulls if isinstance(v, (int, float)) and not isinstance(v, bool)]

            summary: Dict[str, Any] = {
                "total_rows": len(records),
                "null_count": null_count,
                "distinct_count": len(set(str(v) for v in non_nulls)),
            }

            if len(numeric_vals) == len(non_nulls) and numeric_vals:
                summary["type"] = "numeric"
                summary["min"] = min(numeric_vals)
                summary["max"] = max(numeric_vals)
                summary["mean"] = round(statistics.mean(numeric_vals), 4)
                summary["median"] = round(statistics.median(numeric_vals), 4)
                if len(numeric_vals) > 1:
                    summary["stdev"] = round(statistics.stdev(numeric_vals), 4)
            else:
                summary["type"] = "categorical/string"
                freq = collections.Counter(str(v) for v in non_nulls)
                summary["top_values"] = freq.most_common(3)

            col_summaries[col] = summary

        return {
            "action": "summarize",
            "total_records": len(records),
            "column_count": len(all_columns),
            "columns": col_summaries,
        }
