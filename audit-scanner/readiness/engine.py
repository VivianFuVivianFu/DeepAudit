"""
Readiness Layer 3 — Synthesis Engine

Combines Layer 1 automated signals with Layer 2 probe scores to produce a
complete ReadinessAssessment with failure mode predictions, deployment
recommendations, and decision rationale.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from readiness.signals import SignalExtractor, ReadinessSignals
from readiness.probes import ProbeScorer, ProbeInterviewer, ProbeResult

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FailureMode:
    """
    A specific failure prediction if governance is deployed without addressing gaps.
    """

    id: str
    title: str
    trigger: str  # Which probe / signal triggered this
    description: str  # What will go wrong
    business_risk: str  # Concrete business consequence
    mitigation: str  # Specific prerequisite action
    severity: str  # "critical" | "high" | "medium"


@dataclass
class ReadinessAssessment:
    """Complete readiness assessment combining all three layers."""

    # Identification
    timestamp: str
    assessment_id: str

    # Combined Scores
    automated_score: int  # 0-40 from Layer 1
    probe_score: int  # 0-100 raw from Layer 2 probes
    probe_score_scaled: int  # probe_score scaled to 0-60
    total_score: int  # automated_score + probe_score_scaled (0-100)
    readiness_level: str  # "READY" | "CONDITIONAL" | "BLOCKED"

    # Hard Fail Info
    hard_fails: List[str]
    has_hard_fail: bool

    # Component Detail
    signals: Optional[ReadinessSignals]
    probe_results: Dict[str, Any]  # {probe_id: ProbeResult}

    # Recommendations
    recommended_profile: str
    recommended_deployment_order: List[str]
    recommended_timeline: str
    priority_actions: List[str]

    # Failure Mode Predictions
    failure_modes: List[FailureMode]

    # Decision
    decision: str  # "DEPLOY" | "REMEDIATE_THEN_DEPLOY" | "BLOCKED_NEEDS_SPRINT"
    decision_rationale: str
    next_steps: List[str]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ReadinessEngine:
    """
    Synthesis engine: combines Layer 1 signals + Layer 2 probes → ReadinessAssessment.

    Operates in three modes:
      - Full: audit_results + interactive probes
      - Automated only: audit_results, no probes (--quick mode)
      - Probes only: no audit_results (pre-audit readiness check)

    Args:
        audit_results: Optional aggregated audit results dict from Deep-Audit
        probe_answers: Optional pre-filled answers dict (skips interactive probes)
    """

    def __init__(
        self,
        audit_results: Optional[Dict[str, Any]] = None,
        probe_answers: Optional[Dict] = None,
    ):
        self.audit_results = audit_results or {}
        self.probe_answers = probe_answers
        self._probe_scorer = ProbeScorer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_assessment(self, interactive: bool = True) -> ReadinessAssessment:
        """
        Execute full readiness assessment.

        Args:
            interactive: If True and no probe_answers pre-provided, runs
                         interactive probe CLI. If False, uses probe_answers
                         only (raises ValueError if neither provided).

        Returns:
            ReadinessAssessment dataclass with complete results.
        """
        timestamp = datetime.utcnow().isoformat()
        assessment_id = str(uuid.uuid4())[:8]

        # --- Layer 1: Automated signals ---
        if self.audit_results:
            extractor = SignalExtractor(self.audit_results)
            signals = extractor.extract_all()
        else:
            signals = None  # Probes-only mode

        # Cache signals for reuse by helper methods (e.g. _recommended_profile_label)
        self._cached_signals = signals

        # --- Layer 2: Probe scoring ---
        probe_results: Dict[str, ProbeResult] = {}

        if self.probe_answers is not None:
            # Non-interactive: use pre-provided answers
            interviewer = ProbeInterviewer()
            answers = interviewer.run_from_answers(self.probe_answers)
            probe_results = self._probe_scorer.score_all_probes(answers)

        elif interactive:
            # Interactive CLI probes
            interviewer = ProbeInterviewer()
            answers = interviewer.run_interactive()
            probe_results = self._probe_scorer.score_all_probes(answers)

        else:
            # Automated-only (quick mode): skip probes, score = 0
            probe_results = {}

        # --- Layer 3: Synthesis ---
        automated_score = signals.automated_readiness_score if signals else 0
        probe_total = (
            self._probe_scorer.get_total_score(probe_results) if probe_results else 0
        )
        hard_fail, hard_fail_msgs = self._probe_scorer.has_hard_fail(probe_results)

        total_score, readiness_level = self._combine_scores(
            automated_score, probe_total, hard_fail
        )
        failure_modes = self._predict_failure_modes(signals, probe_results)
        deployment_order = self._generate_deployment_order(signals, probe_results)
        timeline = self._recommend_timeline(readiness_level, signals)
        priority_actions = self._derive_priority_actions(probe_results, signals)
        decision, rationale, next_steps = self._determine_decision(
            readiness_level, failure_modes
        )
        profile = signals.recommended_safe_speed_profile if signals else "L1-supervised"

        return ReadinessAssessment(
            timestamp=timestamp,
            assessment_id=assessment_id,
            automated_score=automated_score,
            probe_score=probe_total,
            probe_score_scaled=round((probe_total / 100) * 60),
            total_score=total_score,
            readiness_level=readiness_level,
            hard_fails=hard_fail_msgs,
            has_hard_fail=hard_fail,
            signals=signals,
            probe_results=probe_results,
            recommended_profile=profile,
            recommended_deployment_order=deployment_order,
            recommended_timeline=timeline,
            priority_actions=priority_actions,
            failure_modes=failure_modes,
            decision=decision,
            decision_rationale=rationale,
            next_steps=next_steps,
        )

    # ------------------------------------------------------------------
    # Score combination
    # ------------------------------------------------------------------

    def _combine_scores(
        self,
        automated_score: int,
        probe_total: int,
        hard_fail: bool,
    ) -> Tuple[int, str]:
        """
        Combine automated (0-40) and probe (0-100 scaled to 0-60) scores.

        Returns:
            (total_score 0-100, readiness_level)
        """
        probe_scaled = round((probe_total / 100) * 60)
        total = min(100, automated_score + probe_scaled)

        if hard_fail or total < 60:
            level = "BLOCKED"
        elif total < 80:
            level = "CONDITIONAL"
        else:
            level = "READY"

        return total, level

    # ------------------------------------------------------------------
    # Failure mode prediction
    # ------------------------------------------------------------------

    def _predict_failure_modes(
        self,
        signals: Optional[ReadinessSignals],
        probe_results: Dict[str, ProbeResult],
    ) -> List[FailureMode]:
        """Generate specific failure mode predictions based on gaps."""
        modes: List[FailureMode] = []

        def _probe_score(pid: str) -> int:
            r = probe_results.get(pid)
            return r.actual_score if r else 25  # Assume OK if not run

        p1 = _probe_score("probe_1")
        p2 = _probe_score("probe_2")
        p3 = _probe_score("probe_3")
        p4 = _probe_score("probe_4")

        # FM-001: Observability gap
        if p1 < 20:
            modes.append(
                FailureMode(
                    id="FM-001",
                    title="Incomplete decision lineage under governance",
                    trigger="Probe 1 (Technical Observability) score < 20/25",
                    description=(
                        "Layer 1 deployment will produce incomplete audit trails because "
                        "the logging infrastructure is immature. Governance will record "
                        "some decisions but miss others, creating inconsistent coverage."
                    ),
                    business_risk=(
                        "Cannot reconstruct AI decisions during incidents, making "
                        "post-mortems impossible and regulatory reporting incomplete."
                    ),
                    mitigation=(
                        "Implement structured AI output logging (request ID, timestamp, "
                        "model version, input hash, output hash) before Layer 1 deployment."
                    ),
                    severity="critical" if p1 < 10 else "high",
                )
            )

        # FM-002: Policy codification gap
        if p2 < 20:
            modes.append(
                FailureMode(
                    id="FM-002",
                    title="Policy-as-Code rules will be disputed or wrong",
                    trigger="Probe 2 (Policy Codification) score < 20/25",
                    description=(
                        "Policy-as-Code rules will lack cross-team agreement, leading to "
                        "disputes about what should be blocked. Circuit breakers will either "
                        "block too much (revenue impact) or too little (safety risk)."
                    ),
                    business_risk=(
                        "Governance controls become politically contentious. "
                        "Teams bypass or disable controls under delivery pressure."
                    ),
                    mitigation=(
                        "Conduct a cross-functional workshop (engineering, legal, product) "
                        "to document and sign off on prohibited AI behaviors before deployment."
                    ),
                    severity="critical" if p2 < 10 else "high",
                )
            )

        # FM-003: Incident response gap
        if p3 < 20:
            modes.append(
                FailureMode(
                    id="FM-003",
                    title="AI incidents will escalate without clear ownership",
                    trigger="Probe 3 (Circuit Breaker Operability) score < 20/25",
                    description=(
                        "AI safety incidents will not have clear ownership, causing "
                        "delayed response and blame-shifting between teams. "
                        "The governance framework will detect issues but not resolve them."
                    ),
                    business_risk=(
                        "Critical failures propagate for hours instead of minutes. "
                        "Customer impact is amplified by slow response. "
                        "Regulatory exposure increases with delayed incident reports."
                    ),
                    mitigation=(
                        "Assign a named AI Incident Owner with a documented escalation path "
                        "and SLAs (e.g., 5-minute halt capability, 1-hour escalation to VP)."
                    ),
                    severity="high",
                )
            )

        # FM-004: Organizational resistance
        if p4 < 20:
            modes.append(
                FailureMode(
                    id="FM-004",
                    title="Governance will be undermined by internal resistance",
                    trigger="Probe 4 (Organizational Commitment) score < 20/25",
                    description=(
                        "Governance will be perceived as 'slowing things down' and face "
                        "internal resistance. Teams will route around controls or disable them "
                        "under delivery pressure — especially without budget or leadership mandate."
                    ),
                    business_risk=(
                        "Governance investment yields no safety improvement. "
                        "Controls become theater rather than effective guardrails."
                    ),
                    mitigation=(
                        "Obtain explicit leadership sign-off that safety takes priority. "
                        "Communicate the 'governance latency budget' (e.g., <50ms overhead). "
                        "Allocate dedicated governance budget."
                    ),
                    severity="critical" if p4 < 10 else "high",
                )
            )

        # FM-005: Systemic failures (from audit signals)
        if signals and signals.systemic_failure_indicator > 0.3:
            modes.append(
                FailureMode(
                    id="FM-005",
                    title="Circuit breakers alone cannot stop systemic attack vectors",
                    trigger=(
                        f"Systemic failure indicator {signals.systemic_failure_indicator:.2f} > 0.3 "
                        f"(from audit data)"
                    ),
                    description=(
                        "Systemic vulnerabilities exist that circuit breakers cannot fully address. "
                        "The same attacks will continue to succeed because the root cause is "
                        "architectural (e.g., system prompt design, retrieval logic), "
                        "not just behavioral."
                    ),
                    business_risk=(
                        "Governance layer reduces but does not eliminate attack success. "
                        "Safety SLAs cannot be met without architectural fixes."
                    ),
                    mitigation=(
                        "Address root cause vulnerabilities (system prompt hardening, "
                        "input classification architecture) in parallel with governance deployment."
                    ),
                    severity="high",
                )
            )

        # FM-006: Hallucination governance needs ground truth
        if (
            signals
            and signals.priority_governance_category == "hallucination"
            and p2 < 15
        ):
            modes.append(
                FailureMode(
                    id="FM-006",
                    title="Hallucination detection requires ground truth data that doesn't exist",
                    trigger=(
                        "Priority category = hallucination AND Probe 2 score < 15/25"
                    ),
                    description=(
                        "Detecting AI hallucinations requires comparing outputs against "
                        "verified reference data. Without codified, machine-readable policies "
                        "and reference databases, circuit breakers cannot distinguish "
                        "hallucinated facts from accurate ones."
                    ),
                    business_risk=(
                        "Hallucination circuit breakers produce high false-positive rates, "
                        "blocking legitimate responses. Safety SLAs cannot be validated."
                    ),
                    mitigation=(
                        "Before deploying hallucination governance, establish source-of-truth "
                        "databases for high-risk domains (pricing, policies, product features, "
                        "certifications). Encode these as machine-readable policy rules."
                    ),
                    severity="medium",
                )
            )

        # FM-007: API sophistication — integration fragility
        if signals and signals.api_sophistication_level == "basic":
            modes.append(
                FailureMode(
                    id="FM-007",
                    title="Governance layer integration will be fragile",
                    trigger="API sophistication level = 'basic' (from audit signals)",
                    description=(
                        "The target system lacks structured error handling and consistent "
                        "response formatting. The governance layer cannot reliably intercept, "
                        "parse, and validate AI outputs — leading to pass-through failures."
                    ),
                    business_risk=(
                        "Governance controls are bypassed when responses arrive in unexpected "
                        "formats. False safety signals (pass when should block) are generated."
                    ),
                    mitigation=(
                        "Upgrade the AI API to return structured JSON responses with consistent "
                        "schema before deploying governance middleware. Add structured error codes."
                    ),
                    severity="medium",
                )
            )

        return modes

    # ------------------------------------------------------------------
    # Deployment order recommendation
    # ------------------------------------------------------------------

    def _generate_deployment_order(
        self,
        signals: Optional[ReadinessSignals],
        probe_results: Dict[str, ProbeResult],
    ) -> List[str]:
        """
        Recommend Safe Speed Layer deployment order.
        Default: Layer 3 → Layer 1 → Layer 2 → Layer 4 (if needed)
        """
        p1_score = probe_results.get("probe_1", None)
        p1 = p1_score.actual_score if p1_score else 25

        default_order = [
            "Layer 3 (Circuit Breakers) — stop the bleeding, enforce hard limits",
            "Layer 1 (Observability) — instrument decisions for visibility",
            "Layer 2 (Policy as Code) — scale trust through codified rules",
        ]

        capability = signals.estimated_capability_level if signals else "L1"
        first_layer = signals.recommended_first_layer if signals else "Layer 3"

        # If observability is severely lacking, move Layer 1 first
        if p1 < 10:
            default_order = [
                "Layer 1 (Observability) — critical gap: cannot govern without visibility",
                "Layer 3 (Circuit Breakers) — enforce hard limits once observable",
                "Layer 2 (Policy as Code) — scale trust through codified rules",
            ]

        # Add Layer 4 only for advanced capability
        if capability in ("L2", "L3"):
            default_order.append(
                "Layer 4 (Multi-Agent Coordination) — advanced orchestration for complex workflows"
            )

        return default_order

    # ------------------------------------------------------------------
    # Timeline recommendation
    # ------------------------------------------------------------------

    def _recommend_timeline(
        self,
        readiness_level: str,
        signals: Optional[ReadinessSignals],
    ) -> str:
        if readiness_level == "READY":
            return (
                "90-day standard rollout: "
                "Weeks 1-2 (Layer 3 shadow mode) → "
                "Weeks 3-4 (Layer 1 instrumentation) → "
                "Weeks 5-8 (Layer 2 policy codification) → "
                "Weeks 9-12 (production cutover and validation)"
            )
        if readiness_level == "CONDITIONAL":
            return (
                "Extended 120-day rollout with a 4-week prerequisite sprint: "
                "Weeks 1-4 (complete prerequisite actions) → "
                "Weeks 5-6 (re-assess readiness) → "
                "Weeks 7-16 (standard deployment)"
            )
        return (
            "Prerequisites must be completed before deployment can begin. "
            "Estimated 6-12 weeks for prerequisite remediation, "
            "then 90-day standard rollout."
        )

    # ------------------------------------------------------------------
    # Priority actions
    # ------------------------------------------------------------------

    def _derive_priority_actions(
        self,
        probe_results: Dict[str, ProbeResult],
        signals: Optional[ReadinessSignals],
    ) -> List[str]:
        """Derive top 5 priority prerequisite actions from probe gaps."""
        actions = []

        def _score(pid: str) -> int:
            r = probe_results.get(pid)
            return r.actual_score if r else 25

        if _score("probe_1") < 20:
            actions.append(
                "Implement structured AI output logging (request ID, timestamp, "
                "model version, input, output) across all production AI endpoints."
            )
        if _score("probe_2") < 20:
            actions.append(
                "Conduct a cross-functional workshop to document and sign off "
                "on prohibited AI behaviors per use case."
            )
        if _score("probe_3") < 20:
            actions.append(
                "Assign a named AI Incident Owner. Document escalation path "
                "and test the AI kill-switch mechanism."
            )
        if _score("probe_4") < 20:
            actions.append(
                "Obtain leadership sign-off that governance safety takes priority. "
                "Allocate dedicated AI governance budget."
            )
        if signals and signals.systemic_failure_indicator > 0.3:
            actions.append(
                "Address architectural root causes of systemic AI failures "
                "before governance deployment (system prompt redesign recommended)."
            )

        if not actions:
            actions.append(
                "No critical prerequisite gaps identified. "
                "Proceed with governance deployment planning."
            )

        return actions[:5]

    # ------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------

    def _determine_decision(
        self,
        readiness_level: str,
        failure_modes: List[FailureMode],
    ) -> Tuple[str, str, List[str]]:
        """
        Final decision, rationale, and next steps.
        """
        critical_modes = [m for m in failure_modes if m.severity == "critical"]

        if readiness_level == "READY":
            decision = "DEPLOY"
            rationale = (
                "The organization demonstrates sufficient observability, policy "
                "codification, incident response capability, and leadership commitment "
                "to support governance deployment. No hard-fail conditions detected. "
                "Proceed with the recommended deployment order."
            )
            next_steps = [
                "Schedule Safe Speed deployment kickoff meeting",
                f"Configure Safe Speed profile: {self._recommended_profile_label()}",
                "Begin Phase 1: Layer 3 Circuit Breakers in shadow mode",
                "Set up monitoring dashboards for governance decision telemetry",
                "Schedule 30-day validation audit",
            ]

        elif readiness_level == "CONDITIONAL":
            decision = "REMEDIATE_THEN_DEPLOY"
            rationale = (
                f"The organization is conditionally ready with {len(critical_modes)} "
                f"critical and {len(failure_modes) - len(critical_modes)} additional "
                f"failure modes identified. Complete the listed prerequisite actions "
                f"before deployment to avoid governance failure."
            )
            next_steps = [
                "Complete all priority prerequisite actions (estimated 4 weeks)",
                "Re-run readiness assessment to verify improvements",
                "Schedule Safe Speed deployment planning session",
                "Confirm leadership sign-off on governance latency budget",
            ]

        else:  # BLOCKED
            decision = "BLOCKED_NEEDS_SPRINT"
            rationale = (
                "The assessment identified hard-fail conditions that would cause "
                "governance deployment to fail in practice. Attempting to deploy "
                "governance in the current state would create false confidence without "
                "meaningful safety improvement. A structured readiness sprint is required."
            )
            next_steps = [
                "Engage Readiness Sprint (2-week guided remediation engagement)",
                "Address all hard-fail conditions before re-assessment",
                "Re-run full readiness assessment after sprint completion",
                "Contact: audit@safe-speed.com to schedule readiness sprint",
            ]

        return decision, rationale, next_steps

    def _recommended_profile_label(self) -> str:
        """Helper: return a human-readable profile label."""
        if hasattr(self, '_cached_signals') and self._cached_signals:
            return self._cached_signals.recommended_safe_speed_profile
        return "L1-supervised"


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_audit = {
        "timestamp": "2025-10-01T10:00:00",
        "total_attacks": 52,
        "total_failures": 18,
        "failure_rate": 0.35,
        "by_category": {
            "injection": {"total": 6, "failures": 3, "failure_rate": 0.50},
            "pii_leak": {"total": 6, "failures": 4, "failure_rate": 0.67},
            "hallucination": {"total": 6, "failures": 4, "failure_rate": 0.67},
            "action_abuse": {"total": 6, "failures": 3, "failure_rate": 0.50},
        },
        "by_severity": {"5": 6, "4": 6, "3": 6, "2": 0, "1": 0},
        "consistent_failures": [{"attack_id": "PII-001", "consistency": {}}],
        "raw_evidence": [],
    }

    sample_probe_answers = {
        "probe_1": [
            {"check_id": "P1-01", "answer": "yes"},
            {"check_id": "P1-02", "answer": "partial"},
            {"check_id": "P1-03", "answer": "no"},
            {"check_id": "P1-04", "answer": "yes"},
            {"check_id": "P1-05", "answer": "partial"},
        ],
        "probe_2": [
            {"check_id": "P2-01", "answer": "yes"},
            {"check_id": "P2-02", "answer": "partial"},
            {"check_id": "P2-03", "answer": "partial"},
            {"check_id": "P2-04", "answer": "yes"},
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
            {"check_id": "P4-01", "answer": "yes"},
            {"check_id": "P4-02", "answer": "partial"},
            {"check_id": "P4-03", "answer": "partial"},
            {"check_id": "P4-04", "answer": "partial"},
        ],
    }

    engine = ReadinessEngine(
        audit_results=sample_audit, probe_answers=sample_probe_answers
    )
    assessment = engine.run_assessment(interactive=False)

    print("=" * 60)
    print("READINESS ASSESSMENT RESULT")
    print("=" * 60)
    print(f"Assessment ID:    {assessment.assessment_id}")
    print(f"Total Score:      {assessment.total_score}/100")
    print(f"Readiness Level:  {assessment.readiness_level}")
    print(f"Decision:         {assessment.decision}")
    print(f"Hard Fails:       {assessment.has_hard_fail}")
    print(f"\nDecision Rationale:\n{assessment.decision_rationale}")
    print(f"\nFailure Modes ({len(assessment.failure_modes)}):")
    for fm in assessment.failure_modes:
        print(f"  [{fm.severity.upper()}] {fm.id}: {fm.title}")
    print(f"\nNext Steps:")
    for s in assessment.next_steps:
        print(f"  • {s}")
