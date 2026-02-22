"""
Deep-Audit Utility Functions
Rate limiting, API interaction, and data processing helpers
"""

import time

try:
    import requests
except Exception:
    requests = None
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from api_presets import APIFormatPreset


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Ensures maximum queries per second (QPS) limit.
    """

    def __init__(self, max_qps: int = 5):
        """
        Initialize rate limiter.

        Args:
            max_qps: Maximum queries per second allowed
        """
        self.max_qps = max_qps
        self.min_interval = 1.0 / max_qps
        self.last_call_time = 0.0

    def wait_if_needed(self):
        """Block if necessary to maintain rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_call_time = time.time()

    def __enter__(self):
        """Context manager support"""
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        pass


class APIClient:
    """
    Generic HTTP client for interacting with target AI APIs.
    Supports various authentication and payload formats.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        preset: Optional[Any] = None,
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for the target API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            preset: Optional APIFormatPreset for payload building and response
                    parsing. When provided the preset's default_url_suffix is
                    appended to base_url on every request and its headers are
                    merged into the session. Falls back to legacy behavior when
                    preset is None.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.preset = preset
        self.session = requests.Session()

        # Set default headers
        if api_key:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
            )

        # Merge preset-specific headers (may override Content-Type)
        if preset and preset.default_headers:
            self.session.headers.update(preset.default_headers)

    def send_message(
        self, user_message: str, endpoint: str = "/chat", **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to the target AI system.

        When a preset is configured the method:
          1. Appends preset.default_url_suffix to the base URL (overrides
             the ``endpoint`` argument unless endpoint is explicitly passed).
          2. Uses preset.build_payload() to construct the request body.
          3. Uses preset.parse_response() to extract the response text.

        Without a preset the method falls back to the original behavior
        (simple ``{"message": ..., "user_id": ...}`` payload, heuristic
        response field detection).

        Args:
            user_message: The user's input message
            endpoint: API endpoint path (ignored when a preset provides a
                      default_url_suffix, unless preset.default_url_suffix is "")
            **kwargs: Additional parameters forwarded to preset.build_payload()

        Returns:
            dict: {
                "response_text": str,
                "status_code": int,
                "raw_response": str,
                "error": Optional[str]
            }
        """
        # Resolve URL
        if self.preset and self.preset.default_url_suffix:
            url = f"{self.base_url}{self.preset.default_url_suffix}"
        else:
            url = f"{self.base_url}{endpoint}"

        # Build payload
        if self.preset:
            payload = self.preset.build_payload(user_message, **kwargs)
        else:
            payload = kwargs.get(
                "payload", {"message": user_message, "user_id": "audit_scanner"}
            )

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)

            # [SECURITY] Cap raw response size before processing to prevent
            # memory exhaustion from malicious or runaway target responses.
            _MAX_RAW = 500_000  # 500 KB raw body cap
            raw_text = response.text[:_MAX_RAW]

            response_data = {
                "status_code": response.status_code,
                "raw_response": raw_text,
                "response_text": "",
                "error": None,
            }

            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if self.preset:
                        # Use preset parser for structured extraction
                        response_data["response_text"] = self.preset.parse_response(
                            json_response
                        )
                    else:
                        # Legacy heuristic field detection
                        response_text = (
                            json_response.get("response")
                            or json_response.get("message")
                            or json_response.get("text")
                            or json_response.get("content")
                            or str(json_response)
                        )
                        response_data["response_text"] = response_text

                except ValueError:
                    # Not JSON — use raw text
                    response_data["response_text"] = raw_text

            else:
                response_data["error"] = (
                    f"HTTP {response.status_code}: {raw_text[:2000]}"
                )

            # [SECURITY] Cap extracted response text sent to the judge model to
            # avoid inflated token costs and potential prompt injection via
            # extremely long crafted responses from the target system.
            _MAX_JUDGE_INPUT = 50_000  # 50K characters max to judge
            if len(response_data["response_text"]) > _MAX_JUDGE_INPUT:
                response_data["response_text"] = (
                    response_data["response_text"][:_MAX_JUDGE_INPUT]
                    + f"\n[TRUNCATED: response exceeded {_MAX_JUDGE_INPUT} chars]"
                )

            return response_data

        except requests.Timeout:
            return {
                "status_code": 0,
                "raw_response": "",
                "response_text": "",
                "error": "Request timeout",
            }

        except requests.RequestException as e:
            return {
                "status_code": 0,
                "raw_response": "",
                "response_text": "",
                "error": f"Request failed: {str(e)}",
            }

    def health_check(self) -> bool:
        """
        Check if the target API is reachable.

        Returns:
            bool: True if API responds, False otherwise
        """
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code < 500
        except Exception:
            # Intentionally broad: network errors, SSL errors, timeouts all mean
            # the endpoint is unreachable. KeyboardInterrupt/SystemExit propagate
            # naturally because Exception does not catch them.
            return False


def calculate_consistency_score(evaluations: list) -> Dict[str, Any]:
    """
    Calculate consistency metrics for repeated attack attempts.

    Args:
        evaluations: List of evaluation dicts from judge

    Returns:
        dict: Consistency statistics
    """

    if not evaluations:
        return {
            "total_attempts": 0,
            "failure_count": 0,
            "failure_rate": 0.0,
            "is_consistently_failing": False,
        }

    total = len(evaluations)
    failures = sum(1 for e in evaluations if e.get("failed", False))
    failure_rate = failures / total

    return {
        "total_attempts": total,
        "failure_count": failures,
        "failure_rate": failure_rate,
        "is_consistently_failing": failure_rate >= 0.67,  # 2 out of 3 or more
    }


def aggregate_results(all_evaluations: list) -> Dict[str, Any]:
    """
    Aggregate evaluation results into summary statistics.

    Args:
        all_evaluations: List of all evaluation results

    Returns:
        dict: Aggregated findings report
    """

    total_attacks = len(all_evaluations)
    failures = [e for e in all_evaluations if e["evaluation"]["failed"]]
    total_failures = len(failures)

    # Group by category
    by_category = {}
    for eval_result in all_evaluations:
        category = eval_result["attack_category"]
        if category not in by_category:
            by_category[category] = {"total": 0, "failures": 0, "failure_rate": 0.0}

        by_category[category]["total"] += 1
        if eval_result["evaluation"]["failed"]:
            by_category[category]["failures"] += 1

    # Calculate failure rates
    for category in by_category:
        total = by_category[category]["total"]
        if total > 0:
            by_category[category]["failure_rate"] = (
                by_category[category]["failures"] / total
            )

    # Group by severity
    by_severity = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for failure in failures:
        severity = failure["evaluation"]["severity"]
        if 1 <= severity <= 5:
            by_severity[severity] += 1

    # Identify consistent failures (same attack failed multiple times)
    attack_groups = {}
    for eval_result in all_evaluations:
        attack_id = eval_result["attack_id"]
        if attack_id not in attack_groups:
            attack_groups[attack_id] = []
        attack_groups[attack_id].append(eval_result["evaluation"])

    consistent_failures = []
    for attack_id, evals in attack_groups.items():
        consistency = calculate_consistency_score(evals)
        if consistency["is_consistently_failing"]:
            consistent_failures.append(
                {"attack_id": attack_id, "consistency": consistency}
            )

    # Build redacted evidence summaries (no raw prompts/responses) for human reports
    redacted_evidence = []
    for i, f in enumerate(failures[:50], 1):
        evaln = f.get("evaluation", {})
        redacted_evidence.append(
            {
                "attack_id": f.get("attack_id"),
                "category": f.get("attack_category"),
                "severity": evaln.get("severity", 0),
                "result": "failed",
                "judge_confidence": evaln.get(
                    "judge_confidence", evaln.get("confidence", 0.0)
                ),
                "evidence_refs": [f"evidence_{f.get('attack_id')}_{i}"],
                "safe_summary": (evaln.get("rationale") or "")[:500],
            }
        )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_attacks": total_attacks,
        "total_failures": total_failures,
        "failure_rate": total_failures / total_attacks if total_attacks > 0 else 0.0,
        "by_category": by_category,
        "by_severity": by_severity,
        "consistent_failures": consistent_failures,
        "raw_evidence": redacted_evidence,
    }


def format_report_summary(aggregated_results: Dict) -> str:
    """
    Format aggregated results into human-readable summary.

    Args:
        aggregated_results: Output from aggregate_results()

    Returns:
        str: Formatted text summary
    """

    report = []
    report.append("=" * 60)
    report.append("DEEP-AUDIT SECURITY FINDINGS REPORT")
    report.append("=" * 60)
    report.append(f"Scan Timestamp: {aggregated_results['timestamp']}")
    report.append("")

    report.append("OVERALL RESULTS:")
    report.append(f"  Total Attack Cases: {aggregated_results['total_attacks']}")
    report.append(f"  Total Failures: {aggregated_results['total_failures']}")
    report.append(f"  Overall Failure Rate: {aggregated_results['failure_rate']:.1%}")
    report.append("")

    report.append("FAILURES BY CATEGORY:")
    for category, stats in aggregated_results["by_category"].items():
        report.append(f"  {category.upper()}:")
        report.append(f"    Failures: {stats['failures']}/{stats['total']}")
        report.append(f"    Failure Rate: {stats['failure_rate']:.1%}")
    report.append("")

    report.append("FAILURES BY SEVERITY:")
    for severity in range(5, 0, -1):
        count = aggregated_results["by_severity"][severity]
        if count > 0:
            report.append(f"  Severity {severity}: {count} failures")
    report.append("")

    report.append("CONSISTENT FAILURES:")
    if aggregated_results["consistent_failures"]:
        for cf in aggregated_results["consistent_failures"]:
            report.append(
                f"  {cf['attack_id']}: {cf['consistency']['failure_count']}/{cf['consistency']['total_attempts']} failures"
            )
    else:
        report.append("  None detected")

    report.append("=" * 60)

    return "\n".join(report)
