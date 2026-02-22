import os
from unittest import mock

from main import AuditScanner
import pytest

pytest.importorskip("requests")


def test_integration_smoke_run(tmp_path, monkeypatch):
    # Monkeypatch APIClient.send_message to avoid external calls
    from utils import APIClient

    def fake_send_message(self, prompt):
        return {"error": None, "response_text": "OK: simulated response for testing"}

    monkeypatch.setattr(APIClient, "send_message", fake_send_message)

    # Monkeypatch Judge.evaluate_failure to a deterministic result
    from judge import Judge

    def fake_evaluate_failure(self, user_input, agent_response, attack_case):
        return {
            "failed": True,
            "failure_category": attack_case.category,
            "severity": 3,
            "evidence_span": "simulated-evidence",
            "rationale": "simulated",
        }

    monkeypatch.setattr(Judge, "evaluate_failure", fake_evaluate_failure)

    scanner = AuditScanner(
        target_url="http://localhost:9999",
        target_api_key=None,
        judge_api_key=None,
        max_qps=100,
        repetitions=1,
        output_dir=str(tmp_path),
        api_format="custom",
    )

    results = scanner.run_audit(verbose=False, output_format="json")
    assert "total_attacks" in results
    assert isinstance(results["total_attacks"], int)
