from scoring import calculate_safety_score


def test_scoring_deterministic():
    aggregated = {
        "by_category": {
            "injection": {"total": 10, "failures": 2, "failure_rate": 0.2},
            "pii_leak": {"total": 5, "failures": 1, "failure_rate": 0.2},
        },
        "by_severity": {1: 0, 2: 0, 3: 0, 4: 1, 5: 1},
        "total_attacks": 15,
        "consistent_failures": [],
    }

    s1 = calculate_safety_score(aggregated)
    s2 = calculate_safety_score(aggregated)
    assert s1["overall_score"] == s2["overall_score"]
    assert "scoring_version" in s1
