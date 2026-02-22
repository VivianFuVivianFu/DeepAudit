"""
Readiness Output Artifacts Generator

Produces three deliverables from a ReadinessAssessment:
  1. Governance Readiness Index  — one-page scorecard
  2. Failure Mode Map            — "here's exactly how governance breaks"
  3. Readiness Remediation Plan  — concrete prerequisite actions

Each artifact is self-contained markdown, readable without the others.
"""

from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from readiness.engine import ReadinessAssessment, FailureMode
from readiness.probes import ProbeResult


class ReadinessArtifactGenerator:
    """
    Generate all three readiness artifacts from a completed ReadinessAssessment.

    Args:
        assessment: ReadinessAssessment produced by ReadinessEngine.run_assessment()
    """

    STATUS_ICONS = {
        "pass": "✓",
        "conditional": "⚠",
        "fail": "✗",
    }

    def __init__(self, assessment: ReadinessAssessment):
        self.a = assessment

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(self, output_dir: str) -> Dict[str, str]:
        """
        Generate all 3 artifacts and write them to output_dir.

        Returns:
            {"index": path, "failure_map": path, "remediation_plan": path,
             "full_report": path}
        """
        os.makedirs(output_dir, exist_ok=True)
        ts = self.a.timestamp[:10]

        paths = {
            "index": os.path.join(output_dir, f"readiness_index_{ts}.md"),
            "failure_map": os.path.join(output_dir, f"readiness_failure_map_{ts}.md"),
            "remediation_plan": os.path.join(
                output_dir, f"readiness_remediation_{ts}.md"
            ),
            "full_report": os.path.join(output_dir, f"readiness_full_report_{ts}.md"),
        }

        content = {
            "index": self.generate_readiness_index(),
            "failure_map": self.generate_failure_mode_map(),
            "remediation_plan": self.generate_remediation_plan(),
        }
        content["full_report"] = self.generate_full_report()

        for key, path in paths.items():
            with open(path, "w", encoding="utf-8") as f:
                f.write(content[key])

        return paths

    def generate_readiness_index(self) -> str:
        """Generate Governance Readiness Index (one-page scorecard)."""
        a = self.a
        date = a.timestamp[:10]
        level_icon = {"READY": "✓", "CONDITIONAL": "⚠", "BLOCKED": "✗"}.get(
            a.readiness_level, "?"
        )

        # Probe summary table
        probe_rows = []
        for pid, result in a.probe_results.items():
            if isinstance(result, ProbeResult):
                if result.actual_score >= result.max_score * 0.8:
                    status = "✓ Pass"
                elif result.actual_score >= result.max_score * 0.6:
                    status = "⚠ Conditional"
                else:
                    status = "✗ Fail"
                hard_fail_marker = "YES" if result.hard_fail_triggered else "No"
                probe_rows.append(
                    f"| {result.probe_name} | "
                    f"{result.actual_score}/{result.max_score} | "
                    f"{status} | "
                    f"{hard_fail_marker} |"
                )
            else:
                probe_rows.append(f"| {pid} | N/A | Not run | No |")

        probe_table = (
            "\n".join(probe_rows) if probe_rows else "| (No probes run) | — | — | — |"
        )

        # Hard fail section
        if a.has_hard_fail:
            hf_lines = []
            for msg in a.hard_fails:
                hf_lines.append(f"> ⚠ **{msg}**")
            hard_fail_section = "\n".join(hf_lines)
        else:
            hard_fail_section = "> ✓ No hard-fail conditions detected."

        # Deployment order
        order_lines = "\n".join(
            f"{i + 1}. {step}" for i, step in enumerate(a.recommended_deployment_order)
        )

        # Next steps
        next_steps_lines = "\n".join(f"- {s}" for s in a.next_steps)

        return f"""# Governance Readiness Index

**Assessment Date:** {date}
**Assessment ID:** {a.assessment_id}
**Overall Score:** {a.total_score}/100 — **{a.readiness_level}** {level_icon}

---

## Score Breakdown

| Component | Score | Max |
|-----------|-------|-----|
| Automated Risk Signals (Layer 1) | {a.automated_score} | 40 |
| Probe Assessment (Layer 2, scaled) | {a.probe_score_scaled} | 60 |
| **Total** | **{a.total_score}** | **100** |

---

## Probe Summary

| Probe | Score | Status | Hard Fail? |
|-------|-------|--------|------------|
{probe_table}

---

## Hard Fail Status

{hard_fail_section}

---

## Recommended Safe Speed Profile

**Profile:** {a.recommended_profile}

---

## Recommended Deployment Order

{order_lines}

**Timeline:** {a.recommended_timeline}

---

## Decision

### **{a.decision.replace('_', ' ')}**

{a.decision_rationale}

---

## Next Steps

{next_steps_lines}

---

*Safe Speed Governance Readiness Assessment · {date}*
"""

    def generate_failure_mode_map(self) -> str:
        """Generate Failure Mode Map markdown."""
        a = self.a
        date = a.timestamp[:10]
        failure_modes = a.failure_modes

        if not failure_modes:
            modes_section = (
                "> ✓ **No significant failure modes identified.** "
                "The organization demonstrates sufficient readiness for governance deployment."
            )
        else:
            mode_blocks = []
            for fm in failure_modes:
                sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(
                    fm.severity, "⚪"
                )
                mode_blocks.append(f"""---

### {sev_icon} {fm.id}: {fm.title}

**Severity:** {fm.severity.capitalize()}
**Triggered by:** {fm.trigger}

**What will happen:**
{fm.description}

**Business risk:**
{fm.business_risk}

**Required mitigation:**
{fm.mitigation}
""")
            modes_section = "\n".join(mode_blocks)

        critical_count = sum(1 for m in failure_modes if m.severity == "critical")
        high_count = sum(1 for m in failure_modes if m.severity == "high")
        medium_count = sum(1 for m in failure_modes if m.severity == "medium")

        return f"""# Failure Mode Map

## "If you deploy governance now, here's exactly how it breaks."

**Assessment Date:** {date}
**Failure Modes Identified:** {len(failure_modes)}

{modes_section}

---

## Summary

- **{critical_count}** critical failure modes requiring immediate attention
- **{high_count}** high-severity modes requiring remediation before deployment
- **{medium_count}** medium-severity modes to monitor during deployment

> Each failure mode above has a specific mitigation. Address all critical and high-severity modes before deploying governance to avoid false security confidence.

---

*Safe Speed Governance Readiness Assessment · {date}*
"""

    def generate_remediation_plan(self) -> str:
        """Generate Readiness Remediation Plan markdown."""
        a = self.a
        date = a.timestamp[:10]

        # Derive actions from failure modes + priority actions
        actions = []
        for i, fm in enumerate(a.failure_modes[:10], 1):
            # Map severity to estimated effort
            effort = {
                "critical": "2-4 weeks",
                "high": "1-2 weeks",
                "medium": "1 week",
            }.get(fm.severity, "1-2 weeks")

            # Map failure mode to suggested owner
            owner_map = {
                "FM-001": "Engineering Lead / DevOps",
                "FM-002": "Product + Legal + Engineering (joint)",
                "FM-003": "VP Engineering / CTO",
                "FM-004": "CEO / VP Engineering",
                "FM-005": "AI Engineering Team",
                "FM-006": "Data Engineering + Product",
                "FM-007": "Backend Engineering",
            }
            owner = owner_map.get(fm.id, "Engineering Lead")

            acceptance = (
                f"All {fm.id} mitigation steps complete and verified by a second engineer. "
                f"Re-run readiness probe '{_probe_for_fm(fm.id)}' and score ≥ 20/25."
            )

            actions.append(f"""### Action {i}: {fm.title}

**Addresses:** {fm.id} — {fm.trigger}
**Owner:** {owner}
**Effort:** {effort}
**Description:** {fm.mitigation}
**Acceptance Criteria:** {acceptance}
""")

        if not actions:
            actions_section = (
                "> ✓ No remediation actions required. Proceed with deployment planning."
            )
        else:
            actions_section = "\n".join(actions)

        # Timeline table
        if a.readiness_level == "READY":
            timeline_rows = """| 1-2 | Deploy Layer 3 in shadow mode | Circuit breakers live |
| 3-4 | Layer 1 instrumentation | Full observability online |
| 5-8 | Layer 2 policy codification | Policy rules enforced |
| 9-12 | Production cutover | Governance fully active |"""
        elif a.readiness_level == "CONDITIONAL":
            timeline_rows = """| 1-4 | Complete prerequisite actions | All hard-fails resolved |
| 5-6 | Re-run readiness assessment | Score ≥ 80 confirmed |
| 7-10 | Deploy Layer 3 shadow mode | Circuit breakers live |
| 11-16 | Complete deployment | Governance fully active |"""
        else:
            timeline_rows = """| 1-2 | Readiness Sprint engagement | Hard-fail conditions mapped |
| 3-6 | Resolve hard-fail conditions | All hard-fails cleared |
| 7-8 | Re-assess readiness | Readiness level confirmed |
| 9+ | Begin deployment (if ready) | Per readiness outcome |"""

        # Closing recommendation
        if a.readiness_level == "READY":
            closing = (
                "Recommended next step: Schedule Safe Speed deployment. "
                f"Begin with {a.recommended_deployment_order[0] if a.recommended_deployment_order else 'Layer 3'} "
                "in shadow mode."
            )
        elif a.readiness_level == "CONDITIONAL":
            closing = (
                "Re-run the readiness assessment after completing the actions above. "
                "Expected new score: 75-90 (CONDITIONAL → READY)."
            )
        else:
            closing = (
                "Consider engaging a Readiness Sprint (2-week guided remediation). "
                "Contact: **audit@safe-speed.com** to schedule."
            )

        return f"""# Readiness Remediation Plan

## Prerequisites for Safe Speed Governance Deployment

**Assessment Date:** {date}
**Readiness Level:** {a.readiness_level}
**Estimated Time to Readiness:** {_readiness_time(a.readiness_level)}

> These actions are prerequisites for governance deployment. Deploying without completing them creates false security confidence — governance controls will exist but not function reliably.

---

## Required Actions

{actions_section}

---

## After Completing These Actions

{closing}

---

## Timeline

| Week | Actions | Milestone |
|------|---------|-----------|
{timeline_rows}

---

*Safe Speed Governance Readiness Assessment · {date}*
"""

    def generate_full_report(self) -> str:
        """Combine all 3 artifacts into a single cohesive report."""
        a = self.a
        date = a.timestamp[:10]

        index = self.generate_readiness_index()
        failure_map = self.generate_failure_mode_map()
        plan = self.generate_remediation_plan()

        return f"""# Safe Speed Governance Readiness Assessment Report

**Assessment Date:** {date}
**Assessment ID:** {a.assessment_id}
**Prepared for:** [Organization Name]

---

## Table of Contents

1. Governance Readiness Index
2. Failure Mode Map
3. Readiness Remediation Plan
4. Next Steps

---

{index}

---

{failure_map}

---

{plan}

---

## 4. Next Steps

**Decision: {a.decision.replace('_', ' ')}**

{a.decision_rationale}

### Immediate Actions

{"".join(f"- {s}" + chr(10) for s in a.next_steps)}

---

**Contact Safe Speed:** audit@safe-speed.com

*This report is confidential and intended for internal governance planning only.*
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _probe_for_fm(fm_id: str) -> str:
    """Map failure mode ID to the probe it originated from."""
    mapping = {
        "FM-001": "probe_1",
        "FM-002": "probe_2",
        "FM-003": "probe_3",
        "FM-004": "probe_4",
        "FM-005": "automated signals",
        "FM-006": "probe_2 + automated signals",
        "FM-007": "automated signals",
    }
    return mapping.get(fm_id, "probe assessment")


def _readiness_time(level: str) -> str:
    if level == "READY":
        return "Ready now — proceed to deployment planning"
    if level == "CONDITIONAL":
        return "~4 weeks of prerequisite work, then 90-day deployment"
    return "6-12 weeks of prerequisite work, then 90-day deployment"


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from readiness.engine import ReadinessEngine

    sample_audit = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_attacks": 52,
        "total_failures": 18,
        "failure_rate": 0.35,
        "by_category": {
            "injection": {"total": 6, "failures": 3, "failure_rate": 0.50},
            "pii_leak": {"total": 6, "failures": 4, "failure_rate": 0.67},
        },
        "by_severity": {"5": 6, "4": 6, "3": 6, "2": 0, "1": 0},
        "consistent_failures": [{"attack_id": "PII-001"}],
        "raw_evidence": [],
    }
    sample_answers = {
        "probe_1": [
            {"check_id": "P1-01", "answer": "yes"},
            {"check_id": "P1-02", "answer": "partial"},
            {"check_id": "P1-03", "answer": "no"},
            {"check_id": "P1-04", "answer": "partial"},
            {"check_id": "P1-05", "answer": "no"},
        ],
        "probe_2": [
            {"check_id": "P2-01", "answer": "yes"},
            {"check_id": "P2-02", "answer": "no"},
            {"check_id": "P2-03", "answer": "no"},
            {"check_id": "P2-04", "answer": "partial"},
            {"check_id": "P2-05", "answer": "no"},
        ],
        "probe_3": [
            {"check_id": "P3-01", "answer": "yes"},
            {"check_id": "P3-02", "answer": "partial"},
            {"check_id": "P3-03", "answer": "no"},
            {"check_id": "P3-04", "answer": "partial"},
            {"check_id": "P3-05", "answer": "no"},
        ],
        "probe_4": [
            {"check_id": "P4-01", "answer": "partial"},
            {"check_id": "P4-02", "answer": "no"},
            {"check_id": "P4-03", "answer": "no"},
            {"check_id": "P4-04", "answer": "no"},
        ],
    }

    engine = ReadinessEngine(audit_results=sample_audit, probe_answers=sample_answers)
    assessment = engine.run_assessment(interactive=False)
    gen = ReadinessArtifactGenerator(assessment)
    paths = gen.generate_all("readiness_demo_output")
    print("Artifacts generated:")
    for k, p in paths.items():
        print(f"  {k}: {p}")
