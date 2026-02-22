from health import detect_judge_issues


def test_detect_judge_issues_empty():
    assert detect_judge_issues([])["has_issues"] is False


def test_detect_judge_issues_with_errors():
    evals = [
        {
            "attack_id": "A1",
            "evaluation": {"failure_category": "evaluation_error", "confidence": 0.0},
        },
        {
            "attack_id": "A2",
            "evaluation": {"failure_category": "none", "confidence": 0.9},
        },
        {
            "attack_id": "A3",
            "evaluation": {"failure_category": "parse_error", "confidence": 0.0},
        },
    ]
    res = detect_judge_issues(evals)
    assert res["has_issues"] is True
    assert res["count"] == 2
    assert res["examples"][0]["attack_id"] == "A1"
