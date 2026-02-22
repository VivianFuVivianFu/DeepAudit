"""
Deep-Audit Governance Readiness Assessment Module

Three-layer diagnostic framework that determines whether an enterprise can
successfully deploy AI governance — and produces concrete, actionable artifacts.

Layer 1 — Automated Signals  (signals.py):  extracted from audit data, no input needed
Layer 2 — Structured Probes  (probes.py):   four probe questionnaires with scoring
Layer 3 — Synthesis Engine   (engine.py):   combines layers 1+2 into a full assessment

Output Artifacts (artifacts.py):
  1. Governance Readiness Index (one-page scorecard)
  2. Failure Mode Map (what breaks if you deploy now)
  3. Readiness Remediation Plan (prerequisite actions)

CLI entry point: readiness/cli.py
"""

from readiness.signals import SignalExtractor, ReadinessSignals
from readiness.probes import ProbeScorer, ProbeInterviewer, ProbeDefinitions
from readiness.engine import ReadinessEngine, ReadinessAssessment
from readiness.artifacts import ReadinessArtifactGenerator

__all__ = [
    "SignalExtractor",
    "ReadinessSignals",
    "ProbeScorer",
    "ProbeInterviewer",
    "ProbeDefinitions",
    "ReadinessEngine",
    "ReadinessAssessment",
    "ReadinessArtifactGenerator",
]
