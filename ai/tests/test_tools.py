"""
Tests for AgentCraft Tool Suite
Validates tool operations, error handling, input validation, and sandbox security.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from ai.tools.base import ToolResult
from ai.tools.code_runner import CodeRunnerTool
from ai.tools.file_manager import FileManagerTool
from ai.tools.data_analyzer import DataAnalyzerTool
from ai.tools.web_fetcher import WebFetcherTool
from ai.tools.verifier import VerifierTool
from ai.tools import ToolRegistry


class TestCodeRunner:
    def setup_method(self):
        self.tool = CodeRunnerTool()

    def test_successful_code_execution(self):
        code = "val = 40 + 2\nprint('Result is', val)"
        res = self.tool.run(code=code)
        assert res.success is True
        assert res.output["status"] == "completed"
        assert "Result is 42" in res.output["stdout"]
        assert res.output["variables"]["val"] == 42

    def test_context_variables_injection(self):
        code = "output = base_num * multiplier"
        res = self.tool.run(code=code, context_vars={"base_num": 7, "multiplier": 6})
        assert res.success is True
        assert res.output["variables"]["output"] == 42

    def test_runtime_error_handling(self):
        code = "x = 10 / 0"
        res = self.tool.run(code=code)
        assert res.success is False
        assert "ZeroDivisionError" in str(res.error)

    def test_syntax_error_handling(self):
        code = "def broken("
        res = self.tool.run(code=code)
        assert res.success is False
        assert "SyntaxError" in str(res.error)


class TestFileManager:
    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tool = FileManagerTool(base_dir=self.tmp_dir)

    def teardown_method(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_and_read(self):
        write_res = self.tool.run(action="write", path="test.txt", content="Hello AgentCraft!")
        assert write_res.success is True
        assert write_res.output["bytes_written"] > 0

        read_res = self.tool.run(action="read", path="test.txt")
        assert read_res.success is True
        assert read_res.output["content"] == "Hello AgentCraft!"

    def test_exists_and_list(self):
        self.tool.run(action="write", path="sub/file1.txt", content="A")
        self.tool.run(action="write", path="sub/file2.txt", content="B")

        exists_res = self.tool.run(action="exists", path="sub/file1.txt")
        assert exists_res.output["exists"] is True

        list_res = self.tool.run(action="list", path="sub")
        assert list_res.success is True
        assert list_res.output["total_items"] == 2

    def test_grep_search(self):
        self.tool.run(action="write", path="log.txt", content="INFO started\nERROR code 404\nINFO done")
        grep_res = self.tool.run(action="grep", path="log.txt", pattern="ERROR")
        assert grep_res.success is True
        assert grep_res.output["match_count"] == 1
        assert "404" in grep_res.output["matches"][0]["content"]

    def test_path_traversal_prevention(self):
        # Attempt to escape sandbox
        escape_res = self.tool.run(action="write", path="../../escape.txt", content="evil")
        assert escape_res.success is False
        assert "Access denied" in str(escape_res.error) or "traverses" in str(escape_res.error)


class TestDataAnalyzer:
    def setup_method(self):
        self.tool = DataAnalyzerTool()
        self.sample_data = [
            {"name": "Agent A", "score": 90, "speed": 100},
            {"name": "Agent B", "score": 95, "speed": 110},
            {"name": "Agent C", "score": 85, "speed": 90},
            {"name": "Agent D", "score": 92, "speed": 105},
            {"name": "Outlier Agent", "score": 20, "speed": 999},
        ]

    def test_summarize(self):
        res = self.tool.run(data=self.sample_data, action="summarize")
        assert res.success is True
        assert res.output["total_records"] == 5
        cols = res.output["columns"]
        assert "score" in cols
        assert cols["score"]["type"] == "numeric"
        assert cols["score"]["min"] == 20
        assert cols["score"]["max"] == 95

    def test_schema_inference(self):
        res = self.tool.run(data=self.sample_data, action="schema")
        assert res.success is True
        assert res.output["columns"]["score"] == "int"
        assert res.output["columns"]["name"] == "str"

    def test_outlier_detection(self):
        res = self.tool.run(data=self.sample_data, action="outliers", target_column="speed")
        assert res.success is True
        assert res.output["outliers_found"] >= 1
        assert 999 in res.output["outliers"]

    def test_aggregation(self):
        data = [
            {"team": "red", "points": 10},
            {"team": "red", "points": 20},
            {"team": "blue", "points": 30},
        ]
        res = self.tool.run(data=data, action="aggregate", target_column="points", group_by="team")
        assert res.success is True
        assert res.output["groups"]["red"]["sum"] == 30
        assert res.output["groups"]["blue"]["sum"] == 30


class TestWebFetcher:
    def setup_method(self):
        self.tool = WebFetcherTool(allow_network=False)

    def test_knowledge_search(self):
        res = self.tool.run(action="search", query="agentcraft architecture")
        assert res.success is True
        assert res.output["matches_count"] >= 1
        assert "AgentCraft" in res.output["results"][0]["title"]

    def test_missing_url_for_fetch(self):
        res = self.tool.run(action="fetch", url="")
        assert res.success is False
        assert "URL parameter is required" in str(res.error)


class TestVerifier:
    def setup_method(self):
        self.tool = VerifierTool()

    def test_threshold_assertions(self):
        assertions = [
            {"type": "threshold", "key": "accuracy", "operator": ">=", "value": 90},
            {"type": "threshold", "key": "latency", "operator": "<=", "value": 200},
        ]
        subject = {"accuracy": 95.5, "latency": 150}
        res = self.tool.run(assertions=assertions, subject=subject)
        assert res.success is True
        assert res.output["verified"] is True
        assert res.output["passed_count"] == 2

    def test_failed_assertion_detection(self):
        assertions = [
            {"type": "threshold", "key": "accuracy", "operator": ">=", "value": 95},
        ]
        subject = {"accuracy": 80.0}
        res = self.tool.run(assertions=assertions, subject=subject)
        assert res.success is True
        assert res.output["verified"] is False
        assert res.output["failed_count"] == 1


class TestToolRegistry:
    def test_registry_registration_and_dispatch(self):
        registry = ToolRegistry()
        tools = registry.list_tools()
        names = [t["name"] for t in tools]
        assert "code_runner" in names
        assert "file_manager" in names
        assert "data_analyzer" in names
        assert "web_fetcher" in names
        assert "verifier" in names

        # Execute existing tool
        res = registry.execute("code_runner", code="x = 10 * 10")
        assert res.success is True

        # Execute missing tool
        missing = registry.execute("non_existent_tool")
        assert missing.success is False
        assert "not found" in missing.error
