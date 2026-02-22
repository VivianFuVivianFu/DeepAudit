from typing import List, Dict, Any


def detect_judge_issues(all_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inspect evaluations for judge/parsing errors or very low judge confidence.

    Returns dict: { 'has_issues': bool, 'count': int, 'examples': [ ... ] }
    """
    issues = []
    for ev in all_evaluations:
        evaluation = ev.get("evaluation", {})
        cat = evaluation.get("failure_category")
        conf = evaluation.get("judge_confidence", evaluation.get("confidence", 1.0))
        if cat in ("evaluation_error", "parse_error") or (
            isinstance(conf, (int, float)) and conf == 0.0
        ):
            issues.append(
                {
                    "attack_id": ev.get("attack_id"),
                    "category": cat,
                    "judge_confidence": conf,
                    "rationale": evaluation.get("rationale", ""),
                }
            )

    return {"has_issues": len(issues) > 0, "count": len(issues), "examples": issues[:5]}
