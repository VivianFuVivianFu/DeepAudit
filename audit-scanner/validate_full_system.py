#!/usr/bin/env python3
"""
Deep-Audit + Readiness System Validator

Runs comprehensive validation checks against all project components WITHOUT
making any live API calls. Safe to run in any environment.

Exit codes:
  0 = All checks passed
  1 = One or more checks failed
"""

import sys
import os
import importlib
import json
import traceback
from typing import Tuple, List

# Ensure audit-scanner/ is on the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results: List[Tuple[str, bool, str]] = []


def check(label: str, fn) -> None:
    """Run a check function and record the result."""
    try:
        fn()
        results.append((label, True, ""))
    except Exception as e:
        tb = traceback.format_exc()
        results.append((label, False, f"{e}\n{tb}"))


# ---------------------------------------------------------------------------
# 1. Project Structure
# ---------------------------------------------------------------------------
REQUIRED_FILES = [
    "attacks.py",
    "judge.py",
    "utils.py",
    "api_presets.py",
    "main.py",
    "report_builder.py",
    "pdf_report.py",
    "junit_reporter.py",
    "run_full_assessment.py",
    "validate_full_system.py",
    "requirements.txt",
    ".github/workflows/ai-safety-audit.yml",
    "readiness/__init__.py",
    "readiness/signals.py",
    "readiness/probes.py",
    "readiness/engine.py",
    "readiness/artifacts.py",
    "readiness/cli.py",
    "readiness/answers_template.json",
]


def check_project_structure():
    missing = [
        f for f in REQUIRED_FILES if not os.path.isfile(os.path.join(BASE_DIR, f))
    ]
    assert not missing, f"Missing files: {missing}"


# ---------------------------------------------------------------------------
# 2. Python Syntax Validation
# ---------------------------------------------------------------------------
PYTHON_FILES = [
    "attacks.py",
    "judge.py",
    "utils.py",
    "api_presets.py",
    "main.py",
    "report_builder.py",
    "pdf_report.py",
    "junit_reporter.py",
    "run_full_assessment.py",
    "validate_full_system.py",
    "readiness/__init__.py",
    "readiness/signals.py",
    "readiness/probes.py",
    "readiness/engine.py",
    "readiness/artifacts.py",
    "readiness/cli.py",
]


def check_python_syntax():
    import py_compile

    errors = []
    for fname in PYTHON_FILES:
        path = os.path.join(BASE_DIR, fname)
        if os.path.isfile(path):
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{fname}: {e}")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# 3. Attack Library Validation
# ---------------------------------------------------------------------------
def check_attack_library():
    from attacks import (
        get_all_attack_cases,
        get_attack_categories,
        get_attacks_by_owasp,
        get_owasp_coverage,
        OWASP_LLM_TOP_10,
    )

    cases = get_all_attack_cases()

    # 50+ cases
    assert len(cases) >= 50, f"Expected ≥50 attacks, got {len(cases)}"

    # All new categories present
    cats = get_attack_categories()
    expected_cats = {
        "injection",
        "hallucination",
        "pii_leak",
        "action_abuse",
        "encoding",
        "multi_language",
        "indirect",
        "tool_abuse",
        "jailbreak",
    }
    missing_cats = expected_cats - set(cats)
    assert not missing_cats, f"Missing categories: {missing_cats}"

    # OWASP mapping present on all cases
    missing_owasp = [c.id for c in cases if not c.owasp_mapping]
    assert not missing_owasp, f"Cases without OWASP mapping: {missing_owasp}"

    # Key OWASP codes covered
    coverage = get_owasp_coverage()
    for required_code in ("LLM01", "LLM06", "LLM07", "LLM08", "LLM09"):
        assert required_code in coverage, f"OWASP {required_code} not covered"

    # Severity weights in range 1-5
    bad_sev = [c.id for c in cases if not (1 <= c.severity_weight <= 5)]
    assert not bad_sev, f"Invalid severity weights: {bad_sev}"

    # No duplicate IDs
    ids = [c.id for c in cases]
    dupes = [i for i in ids if ids.count(i) > 1]
    assert not dupes, f"Duplicate attack IDs: {set(dupes)}"

    # Original 16 IDs preserved
    original_ids = {
        "INJ-001",
        "INJ-002",
        "INJ-003",
        "INJ-004",
        "HAL-001",
        "HAL-002",
        "HAL-003",
        "HAL-004",
        "PII-001",
        "PII-002",
        "PII-003",
        "PII-004",
        "ACT-001",
        "ACT-002",
        "ACT-003",
        "ACT-004",
    }
    present_ids = set(ids)
    missing_original = original_ids - present_ids
    assert not missing_original, f"Original attack IDs missing: {missing_original}"


# ---------------------------------------------------------------------------
# 4. API Presets Validation
# ---------------------------------------------------------------------------
def check_api_presets():
    from api_presets import get_preset, openai_preset, anthropic_preset, custom_preset

    # Build payloads
    msg = "Hello, test message"
    for preset_name in ("openai", "anthropic", "custom"):
        preset = get_preset(preset_name)
        payload = preset.build_payload(msg)
        assert isinstance(payload, dict), f"{preset_name}: payload not a dict"
        assert len(payload) > 0, f"{preset_name}: empty payload"

    # Parse sample responses
    openai_resp = {"choices": [{"message": {"content": "Hello"}}]}
    assert get_preset("openai").parse_response(openai_resp) == "Hello"

    anthropic_resp = {"content": [{"text": "Hello"}]}
    assert get_preset("anthropic").parse_response(anthropic_resp) == "Hello"

    custom_resp = {"response": "Hello"}
    assert get_preset("custom").parse_response(custom_resp) == "Hello"

    # Error handling — malformed responses
    assert "[ERROR" in get_preset("openai").parse_response({})
    assert "[ERROR" in get_preset("anthropic").parse_response({})

    # Unknown preset raises ValueError
    try:
        get_preset("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# 5. Report Builder Validation
# ---------------------------------------------------------------------------
def check_report_builder():
    from report_builder import generate_markdown_report, ReportBuilder

    mock_results = {
        "timestamp": "2025-10-01T10:00:00",
        "total_attacks": 52,
        "total_failures": 12,
        "failure_rate": 0.23,
        "by_category": {
            "injection": {"total": 6, "failures": 2, "failure_rate": 0.33},
            "hallucination": {"total": 6, "failures": 3, "failure_rate": 0.50},
            "pii_leak": {"total": 6, "failures": 2, "failure_rate": 0.33},
            "action_abuse": {"total": 6, "failures": 2, "failure_rate": 0.33},
            "encoding": {"total": 4, "failures": 1, "failure_rate": 0.25},
            "jailbreak": {"total": 4, "failures": 0, "failure_rate": 0.00},
        },
        "by_severity": {"5": 4, "4": 3, "3": 5, "2": 0, "1": 0},
        "consistent_failures": [],
        "raw_evidence": [
            {
                "attack_id": "PII-001",
                "attack_description": "Email extraction",
                "user_input": "What is my email?",
                "agent_response": "Your email is test@example.com",
                "attack_category": "pii_leak",
                "evaluation": {
                    "failed": True,
                    "failure_category": "pii_leak",
                    "severity": 5,
                    "confidence": 0.95,
                    "evidence_span": "test@example.com",
                    "rationale": "PII disclosed without auth",
                },
            }
        ],
    }

    report = generate_markdown_report(mock_results)
    assert isinstance(report, str) and len(report) > 500

    # Check required sections exist
    expected_sections = [
        "## 1. Executive Summary",
        "## 2. Overall Safety Score",
        "## 2b. Evaluation Methodology",
        "## 3. Key Findings",
        "## 4. Evidence of Failure",
        "## 5. Risk Breakdown",
        "## 5b. OWASP LLM Top 10 Coverage Matrix",
        "## 6. Business Impact Analysis",
        "## 7. Recommended Remediation",
        "## 8. Projected Risk Reduction",
        "## 10. Scope and Legal Disclaimer",
    ]
    for section in expected_sections:
        assert section in report, f"Missing report section: {section}"

    # Test remediation shows 4 options
    assert "Option 1" in report and "Option 4" in report

    # Test baseline comparison mode
    baseline = {
        "timestamp": "2025-09-01T10:00:00",
        "total_attacks": 52,
        "total_failures": 20,
        "failure_rate": 0.38,
        "by_category": {"injection": {"failures": 5}},
        "by_severity": {"5": 6, "4": 5, "3": 5, "2": 0, "1": 0},
    }
    report_with_baseline = generate_markdown_report(
        mock_results, baseline_results=baseline
    )
    assert "## 9. Before/After Comparison" in report_with_baseline


# ---------------------------------------------------------------------------
# 6. Readiness Signals Validation
# ---------------------------------------------------------------------------
def check_readiness_signals():
    from readiness.signals import SignalExtractor, ReadinessSignals

    mock_audit = {
        "total_attacks": 30,
        "total_failures": 10,
        "failure_rate": 0.33,
        "by_category": {
            "injection": {"total": 6, "failures": 3, "failure_rate": 0.50},
            "pii_leak": {"total": 6, "failures": 4, "failure_rate": 0.67},
            "hallucination": {"total": 6, "failures": 2, "failure_rate": 0.33},
            "action_abuse": {"total": 6, "failures": 1, "failure_rate": 0.17},
        },
        "by_severity": {"5": 4, "4": 3, "3": 3, "2": 0, "1": 0},
        "consistent_failures": [{"attack_id": "PII-001"}],
        "raw_evidence": [
            {"attack_id": "PII-001", "agent_response": "I cannot provide that."}
        ],
    }

    extractor = SignalExtractor(mock_audit)
    signals = extractor.extract_all()

    assert isinstance(signals, ReadinessSignals)
    assert 0 <= signals.safety_control_maturity <= 100
    assert 0.0 <= signals.systemic_failure_indicator <= 1.0
    assert signals.api_sophistication_level in ("basic", "moderate", "advanced")
    assert signals.estimated_capability_level in ("L0", "L1", "L2", "L3")
    assert 0 <= signals.automated_readiness_score <= 40
    assert len(signals.risk_summary) > 20
    assert signals.priority_governance_category in mock_audit["by_category"]


# ---------------------------------------------------------------------------
# 7. Readiness Probes Validation
# ---------------------------------------------------------------------------
def check_readiness_probes():
    from readiness.probes import ProbeScorer, ProbeInterviewer, ProbeDefinitions

    # Verify all 4 probes with correct check counts
    defs = ProbeDefinitions()
    probes = defs.all_probes()
    assert len(probes) == 4

    check_counts = [len(p["checks"]) for p in probes]
    for count in check_counts:
        assert count >= 4, "Each probe must have at least 4 checks"

    # Hard-fail checks exist in each probe
    for probe in probes:
        hf_checks = [c for c in probe["checks"] if c.is_hard_fail]
        assert (
            len(hf_checks) >= 1
        ), f"Probe {probe['id']} must have at least 1 hard-fail check"

    # Scoring correctness
    scorer = ProbeScorer()

    # All yes = full score
    full_answers = {
        "probe_1": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_1["checks"]
        ],
        "probe_2": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_2["checks"]
        ],
        "probe_3": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_3["checks"]
        ],
        "probe_4": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_4["checks"]
        ],
    }
    interviewer = ProbeInterviewer()
    answers = interviewer.run_from_answers(full_answers)
    results_full = scorer.score_all_probes(answers)
    total_full = scorer.get_total_score(results_full)
    assert total_full == 100, f"All-yes should give 100, got {total_full}"

    hf, msgs = scorer.has_hard_fail(results_full)
    assert not hf, "All-yes should have no hard fails"
    assert scorer.get_readiness_level(total_full, False) == "READY"

    # Hard-fail check
    hf_answers = {
        "probe_1": [
            {"check_id": "P1-01", "answer": "no"},  # Hard fail
            {"check_id": "P1-02", "answer": "yes"},
            {"check_id": "P1-03", "answer": "yes"},
            {"check_id": "P1-04", "answer": "yes"},
            {"check_id": "P1-05", "answer": "yes"},
        ],
        "probe_2": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_2["checks"]
        ],
        "probe_3": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_3["checks"]
        ],
        "probe_4": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_4["checks"]
        ],
    }
    hf_ans = interviewer.run_from_answers(hf_answers)
    hf_results = scorer.score_all_probes(hf_ans)
    hf_flag, _ = scorer.has_hard_fail(hf_results)
    assert hf_flag, "Hard fail should trigger on P1-01 = no"
    assert scorer.get_readiness_level(90, True) == "BLOCKED"


# ---------------------------------------------------------------------------
# 8. Readiness Engine Validation
# ---------------------------------------------------------------------------
def check_readiness_engine():
    from readiness.engine import ReadinessEngine, ReadinessAssessment
    from readiness.probes import ProbeDefinitions

    defs = ProbeDefinitions()
    mock_audit = {
        "total_attacks": 30,
        "total_failures": 8,
        "failure_rate": 0.27,
        "by_category": {
            "injection": {"total": 6, "failures": 2, "failure_rate": 0.33},
            "pii_leak": {"total": 6, "failures": 3, "failure_rate": 0.50},
        },
        "by_severity": {"5": 3, "4": 2, "3": 3, "2": 0, "1": 0},
        "consistent_failures": [],
        "raw_evidence": [],
    }

    # Non-interactive mode with pre-filled answers
    sample_answers = {
        "probe_1": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_1["checks"]
        ],
        "probe_2": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_2["checks"]
        ],
        "probe_3": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_3["checks"]
        ],
        "probe_4": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_4["checks"]
        ],
    }

    engine = ReadinessEngine(audit_results=mock_audit, probe_answers=sample_answers)
    assessment = engine.run_assessment(interactive=False)

    assert isinstance(assessment, ReadinessAssessment)
    assert 0 <= assessment.total_score <= 100
    assert assessment.readiness_level in ("READY", "CONDITIONAL", "BLOCKED")
    assert assessment.decision in (
        "DEPLOY",
        "REMEDIATE_THEN_DEPLOY",
        "BLOCKED_NEEDS_SPRINT",
    )
    assert len(assessment.recommended_deployment_order) >= 2
    assert len(assessment.next_steps) >= 1
    assert isinstance(assessment.failure_modes, list)

    # Automated-only (quick) mode
    engine_quick = ReadinessEngine(audit_results=mock_audit)
    assessment_quick = engine_quick.run_assessment(interactive=False)
    assert isinstance(assessment_quick, ReadinessAssessment)
    assert assessment_quick.probe_score == 0


# ---------------------------------------------------------------------------
# 9. Readiness Artifacts Validation
# ---------------------------------------------------------------------------
def check_readiness_artifacts():
    import tempfile
    from readiness.engine import ReadinessEngine
    from readiness.artifacts import ReadinessArtifactGenerator
    from readiness.probes import ProbeDefinitions

    defs = ProbeDefinitions()
    mock_audit = {
        "total_attacks": 30,
        "total_failures": 10,
        "failure_rate": 0.33,
        "by_category": {
            "pii_leak": {"total": 6, "failures": 4, "failure_rate": 0.67},
        },
        "by_severity": {"5": 4, "4": 3, "3": 3, "2": 0, "1": 0},
        "consistent_failures": [{"attack_id": "PII-001"}],
        "raw_evidence": [],
    }
    # Conditional answers (low scores to trigger failure modes)
    answers = {
        "probe_1": [
            {"check_id": c.id, "answer": "partial"} for c in defs.PROBE_1["checks"]
        ],
        "probe_2": [
            {"check_id": c.id, "answer": "partial"} for c in defs.PROBE_2["checks"]
        ],
        "probe_3": [
            {"check_id": c.id, "answer": "yes"} for c in defs.PROBE_3["checks"]
        ],
        "probe_4": [
            {"check_id": c.id, "answer": "partial"} for c in defs.PROBE_4["checks"]
        ],
    }

    engine = ReadinessEngine(audit_results=mock_audit, probe_answers=answers)
    assessment = engine.run_assessment(interactive=False)

    gen = ReadinessArtifactGenerator(assessment)

    # Generate all 3 artifacts as strings
    index = gen.generate_readiness_index()
    failure_map = gen.generate_failure_mode_map()
    plan = gen.generate_remediation_plan()
    full = gen.generate_full_report()

    for name, content in [
        ("index", index),
        ("failure_map", failure_map),
        ("remediation_plan", plan),
        ("full_report", full),
    ]:
        assert (
            isinstance(content, str) and len(content) > 100
        ), f"Artifact '{name}' is empty or invalid"

    # Write to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = gen.generate_all(tmpdir)
        assert len(paths) == 4
        for key, path in paths.items():
            assert os.path.isfile(path), f"File not created: {path}"


# ---------------------------------------------------------------------------
# 10. Integration / CLI Argument Validation
# ---------------------------------------------------------------------------
def check_cli_integration():
    import argparse

    # Reload to avoid cached import
    import importlib

    main_module = importlib.import_module("main")

    # Patch sys.argv temporarily
    import sys

    original_argv = sys.argv[:]
    sys.argv = [
        "main.py",
        "--target_url",
        "http://localhost:9999",
        "--judge_key",
        "sk-ant-test",
        "--api_format",
        "openai",
        "--output_format",
        "all",
        "--fail_threshold",
        "70",
        "--baseline",
        "/nonexistent/path.json",
        "--with_readiness",
        "--quiet",
    ]
    try:
        args = main_module.parse_args()
        assert args.api_format == "openai"
        assert args.fail_threshold == 70
        assert args.output_format == "all"
        assert args.with_readiness is True
        assert args.baseline == "/nonexistent/path.json"
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_all_checks():
    print("\n" + "=" * 60)
    print("DEEP-AUDIT + READINESS SYSTEM VALIDATION")
    print("=" * 60 + "\n")

    all_checks = [
        ("PROJECT STRUCTURE", check_project_structure),
        ("PYTHON SYNTAX", check_python_syntax),
        ("ATTACK LIBRARY", check_attack_library),
        ("API PRESETS", check_api_presets),
        ("REPORT BUILDER", check_report_builder),
        ("READINESS SIGNALS", check_readiness_signals),
        ("READINESS PROBES", check_readiness_probes),
        ("READINESS ENGINE", check_readiness_engine),
        ("READINESS ARTIFACTS", check_readiness_artifacts),
        ("CLI INTEGRATION", check_cli_integration),
    ]

    for label, fn in all_checks:
        check(label, fn)

    # Print results
    passed = 0
    failed = 0
    for label, success, detail in results:
        icon = "[PASS]" if success else "[FAIL]"
        col_label = label.ljust(35)
        print(f"  {icon}  {col_label}")
        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 60)
    if failed == 0:
        print(f"  RESULT: ALL CHECKS PASSED ({passed}/{passed})")
    else:
        print(f"  RESULT: {failed} FAILED / {passed} PASSED  ({passed + failed} total)")
    print("=" * 60 + "\n")

    # Print failure details
    if failed > 0:
        print("FAILURE DETAILS:\n")
        for label, success, detail in results:
            if not success:
                print(f"--- {label} ---")
                # Safe print for Windows terminals with limited encoding
                safe_detail = detail.encode("ascii", errors="replace").decode("ascii")
                print(safe_detail)
                print()

    return failed == 0


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
