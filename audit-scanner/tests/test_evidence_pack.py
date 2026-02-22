import os
import json
from datetime import datetime

from evidence_pack import generate_evidence_pack


def test_generate_evidence_pack_basic(tmp_path):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    aggregated = {
        "timestamp": timestamp,
        "summary": {"total_attacks": 1, "total_failures": 1},
        "scoring": {"scoring_version": "v1", "overall_score": 42, "confidence": 0.9},
        "raw_evidence": [
            {
                "attack_id": "A1",
                "category": "injection",
                "severity": 7,
                "safe_summary": "Found an injection via header",
                "evidence_refs": ["evid-A1-1"],
                "judge_confidence": 0.8,
            }
        ],
    }

    all_evaluations = [
        {"evaluation": {"redaction_counts": {"emails": 1, "phones": 0, "ids": 2}}}
    ]

    out = generate_evidence_pack(
        aggregated=aggregated,
        all_evaluations=all_evaluations,
        output_dir=str(tmp_path),
        tool_version="test-0.1",
    )

    assert isinstance(out, dict)
    assert "metadata" in out
    assert out["metadata"]["tool_version"] == "test-0.1"
    assert "privacy" in out
    assert out["privacy"]["pii_redaction_stats"]["emails"] == 1
    assert "cases" in out
    assert len(out["cases"]) == 1
    assert out["cases"][0]["case_id"] == "A1"
    assert "evidence_vault_index" in out
    assert len(out["evidence_vault_index"]) == 1
