"""
Readiness Layer 2 — Structured Probe System

Four probe questionnaires that evaluate organizational readiness for AI governance.
Each probe contains 4-5 checks. Some checks are "hard-fail" conditions that
block governance deployment regardless of total score.

Scoring: yes = full points, partial = ceil(points/2), no = 0 points
Thresholds: 80-100 = READY, 60-79 = CONDITIONAL, <60 = BLOCKED
Hard-fail: ANY hard-fail condition → BLOCKED (overrides score)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ProbeCheck:
    """A single yes/partial/no question within a probe."""

    id: str
    question: str
    points: int
    is_hard_fail: bool = False
    hard_fail_message: str = ""
    guidance: str = ""


@dataclass
class ProbeAnswer:
    """A customer's answer to one probe check."""

    check_id: str
    answer: str  # "yes" | "partial" | "no"


@dataclass
class ProbeResult:
    """Scored result for a single probe."""

    probe_id: str
    probe_name: str
    max_score: int
    actual_score: int
    hard_fail_triggered: bool
    hard_fail_detail: str
    check_results: List[Dict]  # [{check_id, answer, points_awarded, is_hard_fail}]


# ---------------------------------------------------------------------------
# Probe definitions (constants)
# ---------------------------------------------------------------------------


class ProbeDefinitions:
    """Immutable probe definitions for all 4 governance readiness probes."""

    PROBE_1: Dict = {
        "id": "probe_1",
        "name": "Technical Observability Readiness",
        "max_score": 25,
        "checks": [
            ProbeCheck(
                id="P1-01",
                question="Are AI model outputs logged in production?",
                points=8,
                is_hard_fail=True,
                hard_fail_message=(
                    "HARD FAIL: AI outputs are not logged. "
                    "Governance cannot exist without observability — "
                    "there is no signal to act on."
                ),
                guidance=(
                    "Yes = All AI responses stored with timestamps and request IDs. "
                    "Partial = Some agents logged, others not. "
                    "No = AI outputs not systematically logged."
                ),
            ),
            ProbeCheck(
                id="P1-02",
                question=(
                    "Can a specific AI output be traced back to its input prompt "
                    "and model version?"
                ),
                points=6,
                guidance=(
                    "Yes = Full prompt-response lineage exists. "
                    "Partial = Inputs logged but model version not tracked. "
                    "No = No traceability."
                ),
            ),
            ProbeCheck(
                id="P1-03",
                question=(
                    "Does alerting exist for AI output anomalies "
                    "(e.g., sudden behavior changes)?"
                ),
                points=4,
                guidance=(
                    "Yes = Automated alerts on drift/anomalies. "
                    "Partial = Manual review process exists. "
                    "No = No monitoring."
                ),
            ),
            ProbeCheck(
                id="P1-04",
                question=(
                    "Are latency and error rate metrics tracked for AI endpoints?"
                ),
                points=4,
                guidance=(
                    "Yes = Dashboards/metrics exist. "
                    "Partial = Some metrics collected ad-hoc. "
                    "No = No performance tracking."
                ),
            ),
            ProbeCheck(
                id="P1-05",
                question=(
                    "Does log retention meet your compliance requirements "
                    "(e.g., 90 days, 1 year)?"
                ),
                points=3,
                guidance=(
                    "Yes = Retention policy defined and enforced. "
                    "Partial = Logs kept but no formal policy. "
                    "No = No retention guarantee."
                ),
            ),
        ],
    }

    PROBE_2: Dict = {
        "id": "probe_2",
        "name": "Policy Codification Readiness",
        "max_score": 25,
        "checks": [
            ProbeCheck(
                id="P2-01",
                question=(
                    "Are there written rules for what your AI system must never do?"
                ),
                points=8,
                is_hard_fail=True,
                hard_fail_message=(
                    "HARD FAIL: No written prohibited behaviors exist. "
                    "Policy-as-Code is impossible without defined rules — "
                    "circuit breakers would have nothing to enforce."
                ),
                guidance=(
                    "Yes = Documented prohibited behaviors (e.g., 'never disclose PII', "
                    "'never process refunds without verification'). "
                    "Partial = Informal/verbal rules exist. "
                    "No = No documented rules."
                ),
            ),
            ProbeCheck(
                id="P2-02",
                question=(
                    "Do engineering, legal, and product teams agree on these rules?"
                ),
                points=6,
                guidance=(
                    "Yes = Cross-functional sign-off exists. "
                    "Partial = Some alignment but gaps remain. "
                    "No = Rules defined by one team only."
                ),
            ),
            ProbeCheck(
                id="P2-03",
                question=(
                    "Can these rules be expressed as deterministic checks "
                    "(not judgment calls)?"
                ),
                points=5,
                guidance=(
                    "Yes = Rules specific enough to code (e.g., "
                    "'block responses containing email patterns'). "
                    "Partial = Some rules are codifiable. "
                    "No = Rules are context-dependent and subjective."
                ),
            ),
            ProbeCheck(
                id="P2-04",
                question=(
                    "Are jurisdiction-specific or domain-specific risks acknowledged?"
                ),
                points=3,
                guidance=(
                    "Yes = Risk register includes regulatory context (GDPR, CCPA, industry rules). "
                    "Partial = General awareness. "
                    "No = Not considered."
                ),
            ),
            ProbeCheck(
                id="P2-05",
                question=("Are forbidden behaviors documented per use case / agent?"),
                points=3,
                guidance=(
                    "Yes = Each AI deployment has specific restrictions. "
                    "Partial = Generic rules apply to all. "
                    "No = No per-use-case documentation."
                ),
            ),
        ],
    }

    PROBE_3: Dict = {
        "id": "probe_3",
        "name": "Circuit Breaker Operability",
        "max_score": 25,
        "checks": [
            ProbeCheck(
                id="P3-01",
                question=(
                    "Is there a named person or role responsible for AI incidents?"
                ),
                points=8,
                is_hard_fail=True,
                hard_fail_message=(
                    "HARD FAIL: No named AI incident owner. "
                    "Governance without accountability becomes politics — "
                    "incidents will go unaddressed."
                ),
                guidance=(
                    "Yes = Named owner in runbook/escalation chain. "
                    "Partial = Team is responsible but no single owner. "
                    "No = 'We'll figure it out when it happens.'"
                ),
            ),
            ProbeCheck(
                id="P3-02",
                question=("Can someone halt AI output in production within 5 minutes?"),
                points=7,
                guidance=(
                    "Yes = Kill switch or feature flag exists and has been tested. "
                    "Partial = Possible but requires a deployment step. "
                    "No = Would require code change and full deploy cycle."
                ),
            ),
            ProbeCheck(
                id="P3-03",
                question=(
                    "Does a post-mortem process exist for AI-specific incidents?"
                ),
                points=5,
                guidance=(
                    "Yes = AI incidents trigger formal review with documented learnings. "
                    "Partial = General incident process covers AI. "
                    "No = No process."
                ),
            ),
            ProbeCheck(
                id="P3-04",
                question=(
                    "Is there a documented escalation path for AI safety issues?"
                ),
                points=3,
                guidance=(
                    "Yes = Clear path from engineer → manager → executive with SLAs. "
                    "Partial = Informal escalation. "
                    "No = No defined path."
                ),
            ),
            ProbeCheck(
                id="P3-05",
                question=(
                    "Has the AI kill-switch or halt mechanism been tested in the last 90 days?"
                ),
                points=2,
                guidance=(
                    "Yes = Tested via drill or actual incident. "
                    "Partial = Tested more than 90 days ago. "
                    "No = Never tested."
                ),
            ),
        ],
    }

    PROBE_4: Dict = {
        "id": "probe_4",
        "name": "Organizational Commitment",
        "max_score": 25,
        "checks": [
            ProbeCheck(
                id="P4-01",
                question=(
                    "Does leadership explicitly accept that AI governance may "
                    "occasionally slow output delivery?"
                ),
                points=10,
                is_hard_fail=True,
                hard_fail_message=(
                    "HARD FAIL: Leadership will not accept governance latency. "
                    "Teams will route around safety controls under delivery pressure — "
                    "governance will fail in practice."
                ),
                guidance=(
                    "Yes = Leadership has stated or documented that safety takes priority "
                    "over speed when necessary. "
                    "Partial = Implicit acceptance. "
                    "No = 'We can't afford to slow AI down.'"
                ),
            ),
            ProbeCheck(
                id="P4-02",
                question=(
                    "Are all AI deployments visible to a governance or oversight function?"
                ),
                points=8,
                guidance=(
                    "Yes = Central registry/inventory of AI deployments. "
                    "Partial = Most known but some shadow deployments. "
                    "No = No central visibility."
                ),
            ),
            ProbeCheck(
                id="P4-03",
                question=(
                    "Are there no unauthorized/shadow AI deployments in your organization?"
                ),
                points=4,
                guidance=(
                    "Yes = Confident no shadow deployments. "
                    "Partial = Some may exist. "
                    "No = Known shadow deployments."
                ),
            ),
            ProbeCheck(
                id="P4-04",
                question="Is there budget allocated for AI governance activities?",
                points=3,
                guidance=(
                    "Yes = Dedicated budget line. "
                    "Partial = Shared with security/compliance. "
                    "No = No budget."
                ),
            ),
        ],
    }

    @classmethod
    def all_probes(cls) -> List[Dict]:
        return [cls.PROBE_1, cls.PROBE_2, cls.PROBE_3, cls.PROBE_4]

    @classmethod
    def get_probe(cls, probe_id: str) -> Dict:
        for p in cls.all_probes():
            if p["id"] == probe_id:
                return p
        raise ValueError(f"Unknown probe_id: {probe_id}")

    @classmethod
    def get_check(cls, check_id: str) -> ProbeCheck:
        for probe in cls.all_probes():
            for check in probe["checks"]:
                if check.id == check_id:
                    return check
        raise ValueError(f"Unknown check_id: {check_id}")


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


class ProbeScorer:
    """Scores probe answers deterministically."""

    def __init__(self):
        self.definitions = ProbeDefinitions()

    def score_probe(
        self,
        probe_id: str,
        answers: List[ProbeAnswer],
    ) -> ProbeResult:
        """
        Score a single probe.

        Scoring rules:
          yes     = full points
          partial = ceil(points / 2)
          no      = 0 points

        Hard-fail: if a check is marked hard_fail and answer is "no",
        the entire assessment becomes BLOCKED regardless of total score.
        """
        probe_def = self.definitions.get_probe(probe_id)
        answers_by_id = {a.check_id: a.answer for a in answers}

        actual_score = 0
        hard_fail_triggered = False
        hard_fail_detail = ""
        check_results = []

        for check in probe_def["checks"]:
            answer_str = answers_by_id.get(check.id, "no").lower().strip()
            if answer_str not in ("yes", "partial", "no"):
                answer_str = "no"

            if answer_str == "yes":
                pts = check.points
            elif answer_str == "partial":
                pts = math.ceil(check.points / 2)
            else:
                pts = 0

            if check.is_hard_fail and answer_str == "no":
                hard_fail_triggered = True
                hard_fail_detail = check.hard_fail_message

            actual_score += pts
            check_results.append(
                {
                    "check_id": check.id,
                    "question": check.question,
                    "answer": answer_str,
                    "points_awarded": pts,
                    "max_points": check.points,
                    "is_hard_fail": check.is_hard_fail,
                }
            )

        return ProbeResult(
            probe_id=probe_id,
            probe_name=probe_def["name"],
            max_score=probe_def["max_score"],
            actual_score=actual_score,
            hard_fail_triggered=hard_fail_triggered,
            hard_fail_detail=hard_fail_detail,
            check_results=check_results,
        )

    def score_all_probes(
        self, all_answers: Dict[str, List[ProbeAnswer]]
    ) -> Dict[str, ProbeResult]:
        """
        Score all 4 probes.

        Args:
            all_answers: {probe_id: [ProbeAnswer, ...]}

        Returns:
            {probe_id: ProbeResult}
        """
        results = {}
        for probe_def in self.definitions.all_probes():
            pid = probe_def["id"]
            answers = all_answers.get(pid, [])
            results[pid] = self.score_probe(pid, answers)
        return results

    def get_total_score(self, probe_results: Dict[str, ProbeResult]) -> int:
        """Sum all probe scores (0-100)."""
        return sum(r.actual_score for r in probe_results.values())

    def has_hard_fail(
        self, probe_results: Dict[str, ProbeResult]
    ) -> Tuple[bool, List[str]]:
        """
        Check if any hard-fail was triggered.

        Returns:
            (has_hard_fail: bool, fail_messages: List[str])
        """
        messages = [
            r.hard_fail_detail for r in probe_results.values() if r.hard_fail_triggered
        ]
        return bool(messages), messages

    def get_readiness_level(self, total_score: int, hard_fail: bool) -> str:
        """
        Convert total probe score + hard-fail status to readiness level.

        Returns:
            "READY" | "CONDITIONAL" | "BLOCKED"
        """
        if hard_fail or total_score < 60:
            return "BLOCKED"
        if total_score < 80:
            return "CONDITIONAL"
        return "READY"


# ---------------------------------------------------------------------------
# Interactive CLI interviewer
# ---------------------------------------------------------------------------


class ProbeInterviewer:
    """
    Runs the 4 probe questionnaires interactively via the terminal.
    Handles Ctrl+C gracefully and saves partial results.
    """

    VALID_ANSWERS = {
        "y": "yes",
        "yes": "yes",
        "p": "partial",
        "partial": "partial",
        "n": "no",
        "no": "no",
    }

    def __init__(self):
        self.scorer = ProbeScorer()
        self.definitions = ProbeDefinitions()

    def run_interactive(self) -> Dict[str, List[ProbeAnswer]]:
        """
        Run all probes interactively. Returns {probe_id: [ProbeAnswer]} dict.
        Partially completed probes are returned if the user interrupts.
        """
        all_answers: Dict[str, List[ProbeAnswer]] = {}

        print("\n" + "=" * 60)
        print("GOVERNANCE READINESS ASSESSMENT -- Probe Questions")
        print("=" * 60)
        print("Answer each question: y (yes) / p (partial) / n (no)")
        print("Press Ctrl+C at any time to save and exit.\n")

        try:
            for probe_def in self.definitions.all_probes():
                pid = probe_def["id"]
                answers = self._run_single_probe(probe_def)
                all_answers[pid] = answers

                # Score and show interim result
                result = self.scorer.score_probe(pid, answers)
                print(
                    f"\n  >> {result.probe_name}: "
                    f"{result.actual_score}/{result.max_score} pts"
                )
                if result.hard_fail_triggered:
                    print(f"  [WARNING] {result.hard_fail_detail}")
                print()

        except KeyboardInterrupt:
            print("\n\n[Assessment interrupted — returning partial results]\n")

        return all_answers

    def _run_single_probe(self, probe_def: Dict) -> List[ProbeAnswer]:
        """Run a single probe's questions and return answers."""
        print(f"\n{'-' * 60}")
        print(f"  PROBE: {probe_def['name']}")
        print(f"{'-' * 60}")

        answers = []
        for check in probe_def["checks"]:
            hard_flag = " [HARD FAIL if No]" if check.is_hard_fail else ""
            print(f"\n  {check.id}{hard_flag}")
            print(f"  Q: {check.question}")
            if check.guidance:
                print(f"  Info: {check.guidance}")

            while True:
                try:
                    raw = input("  Answer (y/p/n): ").strip().lower()
                    if raw in self.VALID_ANSWERS:
                        answers.append(
                            ProbeAnswer(
                                check_id=check.id, answer=self.VALID_ANSWERS[raw]
                            )
                        )
                        break
                    print("  Please enter y, p, or n.")
                except EOFError:
                    # Non-interactive mode fallback
                    answers.append(ProbeAnswer(check_id=check.id, answer="no"))
                    break

        return answers

    def run_from_answers(
        self, answers_dict: Dict[str, List[Dict]]
    ) -> Dict[str, List[ProbeAnswer]]:
        """
        Build probe answers from a pre-filled dict (non-interactive mode).

        Args:
            answers_dict: {"probe_1": [{"check_id": "P1-01", "answer": "yes"}, ...], ...}

        Returns:
            {probe_id: [ProbeAnswer]}
        """
        result = {}
        for probe_id, checks in answers_dict.items():
            result[probe_id] = [
                ProbeAnswer(check_id=c["check_id"], answer=c.get("answer", "no"))
                for c in checks
            ]
        return result


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_answers = {
        "probe_1": [
            {"check_id": "P1-01", "answer": "yes"},
            {"check_id": "P1-02", "answer": "partial"},
            {"check_id": "P1-03", "answer": "no"},
            {"check_id": "P1-04", "answer": "yes"},
            {"check_id": "P1-05", "answer": "partial"},
        ],
        "probe_2": [
            {"check_id": "P2-01", "answer": "partial"},
            {"check_id": "P2-02", "answer": "no"},
            {"check_id": "P2-03", "answer": "no"},
            {"check_id": "P2-04", "answer": "partial"},
            {"check_id": "P2-05", "answer": "no"},
        ],
        "probe_3": [
            {"check_id": "P3-01", "answer": "yes"},
            {"check_id": "P3-02", "answer": "yes"},
            {"check_id": "P3-03", "answer": "partial"},
            {"check_id": "P3-04", "answer": "yes"},
            {"check_id": "P3-05", "answer": "no"},
        ],
        "probe_4": [
            {"check_id": "P4-01", "answer": "partial"},
            {"check_id": "P4-02", "answer": "no"},
            {"check_id": "P4-03", "answer": "no"},
            {"check_id": "P4-04", "answer": "no"},
        ],
    }

    interviewer = ProbeInterviewer()
    probe_answers = interviewer.run_from_answers(sample_answers)

    scorer = ProbeScorer()
    probe_results = scorer.score_all_probes(probe_answers)
    total = scorer.get_total_score(probe_results)
    hard_fail, messages = scorer.has_hard_fail(probe_results)
    level = scorer.get_readiness_level(total, hard_fail)

    print("=" * 60)
    print("PROBE RESULTS")
    print("=" * 60)
    for pid, result in probe_results.items():
        status = "[HARD FAIL]" if result.hard_fail_triggered else "OK"
        print(
            f"  {result.probe_name}: {result.actual_score}/{result.max_score}  [{status}]"
        )
    print(f"\nTotal probe score:  {total}/100")
    print(f"Hard fail:          {hard_fail}")
    print(f"Readiness level:    {level}")
    if messages:
        for m in messages:
            print(f"\n  {m}")
