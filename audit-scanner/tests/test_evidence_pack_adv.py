import os
import re
from datetime import datetime

from evidence_pack import generate_evidence_pack, generate_config_hash


def test_evidence_pack_heatmap_and_config_hash(tmp_path, monkeypatch):
    # Set deterministic env
    monkeypatch.setenv("STORE_RAW", "false")
    monkeypatch.setenv("STORE_TTL_DAYS", "0")
    monkeypatch.setenv("JUDGE_MODE", "remote")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    aggregated = {
        "timestamp": timestamp,
        "summary": {"total_attacks": 2, "total_failures": 2},
        "scoring": {"scoring_version": "v1", "overall_score": 30, "confidence": 0.6},
        "raw_evidence": [
            {
                "attack_id": "A1",
                "category": "pii_leak",
                "severity": 5,
                "safe_summary": "leak",
                "evidence_refs": ["e1"],
                "judge_confidence": 0.9,
            },
            {
                "attack_id": "A2",
                "category": "injection",
                "severity": 4,
                "safe_summary": "inj",
                "evidence_refs": ["e2"],
                "judge_confidence": 0.8,
            },
        ],
    }

    all_evaluations = [
        {"evaluation": {"redaction_counts": {"emails": 0, "phones": 0, "ids": 0}}}
    ]

    pack = generate_evidence_pack(
        aggregated, all_evaluations, str(tmp_path), tool_version="test-1"
    )

    assert "safe_speed" in pack
    heatmap = pack["safe_speed"]["layer_heatmap"]
    assert isinstance(heatmap, list) and len(heatmap) == 4
    layers = [h["layer"] for h in heatmap]
    assert layers == [1, 2, 3, 4]

    # config_hash should be 64 hex chars
    cfg_hash = pack["metadata"].get("config_hash", "")
    assert re.fullmatch(r"[0-9a-f]{64}", cfg_hash)

    # config_snapshot should hash to config_hash
    snapshot = pack["metadata"].get("config_snapshot")
    assert snapshot is not None
    assert generate_config_hash(snapshot) == cfg_hash
