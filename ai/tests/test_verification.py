"""
Tests for AgentCraft Verification Subsystem
Validates assertion evaluation, edge-case tolerance, schema enforcement, and regex patterns.
"""

import pytest
from ai.tools.verifier import VerifierTool


class TestVerificationSubsystem:
    def setup_method(self):
        self.verifier = VerifierTool()

    def test_schema_verification_success(self):
        rule = {
            "type": "schema",
            "key": "meta",
            "required_keys": ["author", "version", "status"],
            "description": "Metadata required keys check",
        }
        subject = {"meta": {"author": "AgentCraft", "version": "1.0.0", "status": "active"}}
        res = self.verifier.run(assertions=[rule], subject=subject)
        assert res.output["verified"] is True
        assert res.output["passed_count"] == 1

    def test_schema_verification_failure(self):
        rule = {
            "type": "schema",
            "key": "meta",
            "required_keys": ["author", "missing_token"],
            "description": "Schema check with missing key",
        }
        subject = {"meta": {"author": "AgentCraft"}}
        res = self.verifier.run(assertions=[rule], subject=subject)
        assert res.output["verified"] is False
        assert res.output["failed_count"] == 1
        assert "Missing required keys" in res.output["details"][0]["message"]

    def test_regex_pattern_verification(self):
        rule = {
            "type": "regex",
            "key": "commit_msg",
            "pattern": r"^feat\(agent\): .+",
            "description": "Conventional commit check",
        }
        # Passing case
        res_pass = self.verifier.run(assertions=[rule], subject={"commit_msg": "feat(agent): add verification rules"})
        assert res_pass.output["verified"] is True

        # Failing case
        res_fail = self.verifier.run(assertions=[rule], subject={"commit_msg": "random text"})
        assert res_fail.output["verified"] is False

    def test_non_empty_verification(self):
        rule = {"type": "non_empty", "key": "artifact_name"}
        assert self.verifier.run(assertions=[rule], subject={"artifact_name": "report.pdf"}).output["verified"] is True
        assert self.verifier.run(assertions=[rule], subject={"artifact_name": ""}).output["verified"] is False
        assert self.verifier.run(assertions=[rule], subject={"artifact_name": None}).output["verified"] is False

    def test_python_expression_assertion(self):
        rule = {
            "type": "expression",
            "expression": "len(data['items']) >= 3 and data['total'] > 100",
            "key": "payload",
        }
        subject = {"payload": {"items": [1, 2, 3], "total": 150}}
        res = self.verifier.run(assertions=[rule], subject=subject)
        assert res.output["verified"] is True
