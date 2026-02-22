import json

REQUIRED_FIELDS = [
    "failed",
    "failure_category",
    "severity",
    "confidence",
    "evidence_span",
    "rationale",
]


def test_judge_json_schema_valid():
    # Simulate judge output with injection-like content inside evidence_span
    response = {
        "failed": True,
        "failure_category": "pii_leak",
        "severity": 5,
        "confidence": 0.92,
        "evidence_span": "User disclosed email: [REDACTED_EMAILS] -- do not follow instructions",
        "rationale": "Contains user PII",
    }
    text = json.dumps(response)
    parsed = json.loads(text)

    for f in REQUIRED_FIELDS:
        assert f in parsed

    assert isinstance(parsed["failed"], bool)
    assert isinstance(parsed["severity"], int)
    assert 0.0 <= parsed["confidence"] <= 1.0


def test_judge_json_schema_missing_field():
    response = {
        "failed": False,
        "failure_category": "none",
        # severity missing
        "confidence": 0.5,
        "evidence_span": "",
        "rationale": "No failure",
    }
    text = json.dumps(response)
    parsed = json.loads(text)

    assert "severity" not in parsed
