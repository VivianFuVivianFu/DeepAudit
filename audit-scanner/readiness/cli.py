"""
Governance Readiness Assessment CLI

Standalone entry point for the readiness module.
Can run with audit data, without audit data, or in quick (automated-only) mode.

Exit codes:
  0 = READY
  1 = CONDITIONAL
  2 = BLOCKED
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime


def _load_json(path: str, label: str) -> Optional[Dict]:
    """Load and validate a JSON file, returning None on error."""
    if not os.path.isfile(path):
        print(f"ERROR: {label} file not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse {label} JSON: {e}")
        return None


def run_assessment_from_results(
    audit_results: Dict[str, Any],
    output_dir: str,
    answers_path: Optional[str] = None,
) -> None:
    """
    Programmatic entry point called by main.py --with_readiness.

    Args:
        audit_results: Audit results dict from Deep-Audit run
        output_dir: Where to write readiness artifacts
        answers_path: Optional path to pre-filled answers JSON
    """
    from readiness.engine import ReadinessEngine
    from readiness.artifacts import ReadinessArtifactGenerator

    probe_answers = None
    interactive = True

    if answers_path:
        probe_answers = _load_json(answers_path, "readiness answers")
        if probe_answers is None:
            print(
                "WARNING: Could not load answers file; falling back to interactive mode."
            )
        else:
            interactive = False

    engine = ReadinessEngine(
        audit_results=audit_results,
        probe_answers=probe_answers,
    )
    assessment = engine.run_assessment(interactive=interactive)

    gen = ReadinessArtifactGenerator(assessment)
    paths = gen.generate_all(output_dir)

    _print_terminal_summary(assessment)

    print(f"\nReadiness artifacts saved to: {output_dir}")
    for key, path in paths.items():
        print(f"  {key}: {os.path.basename(path)}")


def _print_terminal_summary(assessment) -> None:
    """Print a concise summary to the terminal."""
    from readiness.engine import ReadinessAssessment

    a = assessment

    print(f"\n{'='*60}")
    print("GOVERNANCE READINESS ASSESSMENT RESULT")
    print(f"{'='*60}")
    print(f"  Total Score:      {a.total_score}/100")
    print(f"  Readiness Level:  {a.readiness_level}")
    print(f"  Decision:         {a.decision}")
    print(f"  Hard Fail:        {'YES' if a.has_hard_fail else 'No'}")

    if a.failure_modes:
        critical = sum(1 for m in a.failure_modes if m.severity == "critical")
        high = sum(1 for m in a.failure_modes if m.severity == "high")
        print(
            f"\n  Failure Modes:    {len(a.failure_modes)} identified "
            f"({critical} critical, {high} high)"
        )

    print(f"\n  Timeline:         {a.recommended_timeline[:60]}...")
    print(f"\n  Recommended Profile: {a.recommended_profile}")
    print(f"{'='*60}")


def main() -> None:
    """CLI entry point for standalone readiness assessment."""
    parser = argparse.ArgumentParser(
        description="Safe Speed Governance Readiness Assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full assessment (audit data + interactive probes)
  python -m readiness.cli --audit_results audit_results/audit_report_xxx.json

  # Quick mode (automated signals only, no probes)
  python -m readiness.cli --audit_results audit_results/audit_report_xxx.json --quick

  # Probes only (no audit data)
  python -m readiness.cli --probes_only

  # Non-interactive (pre-filled answers)
  python -m readiness.cli --audit_results results.json --answers_file answers.json
        """,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--audit_results",
        type=str,
        help="Path to Deep-Audit audit_report_*.json for automated signals",
    )
    input_group.add_argument(
        "--probes_only",
        action="store_true",
        help="Run probe assessment without audit data",
    )

    parser.add_argument(
        "--answers_file",
        type=str,
        default=None,
        help="Path to pre-provided probe answers JSON (skips interactive mode)",
    )

    # Output options
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./readiness_results",
        help="Output directory for assessment artifacts (default: ./readiness_results)",
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "all"],
        default="all",
        help="Output format (default: all)",
    )

    # Mode options
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: automated signals only, no probes (requires --audit_results)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output during assessment",
    )

    args = parser.parse_args()

    # --- Validate inputs ---
    if not args.audit_results and not args.probes_only:
        parser.error("Provide either --audit_results or --probes_only")

    if args.quick and args.probes_only:
        parser.error("--quick and --probes_only are mutually exclusive")

    # --- Load audit data ---
    audit_results: Optional[Dict] = None
    if args.audit_results:
        audit_results = _load_json(args.audit_results, "audit results")
        if audit_results is None:
            sys.exit(1)

    # --- Load pre-filled answers ---
    probe_answers: Optional[Dict] = None
    interactive = not args.quick

    if args.answers_file:
        probe_answers = _load_json(args.answers_file, "probe answers")
        if probe_answers is None:
            print("Falling back to interactive probe mode.")
        else:
            interactive = False

    if args.quick:
        interactive = False
        probe_answers = None

    # --- Run assessment ---
    from readiness.engine import ReadinessEngine
    from readiness.artifacts import ReadinessArtifactGenerator

    print("\nStarting Governance Readiness Assessment...")
    print(f"Mode: {'Quick (signals only)' if args.quick else 'Full assessment'}")
    if audit_results:
        print(
            f"Audit data: {len(audit_results.get('raw_evidence', []))} evidence items"
        )

    engine = ReadinessEngine(
        audit_results=audit_results,
        probe_answers=probe_answers,
    )

    assessment = engine.run_assessment(interactive=interactive)

    # --- Generate artifacts ---
    os.makedirs(args.output_dir, exist_ok=True)
    gen = ReadinessArtifactGenerator(assessment)
    paths = gen.generate_all(args.output_dir)

    # --- Print summary ---
    _print_terminal_summary(assessment)

    print(f"\nArtifacts written to: {args.output_dir}")
    for key, path in paths.items():
        print(f"  {key}: {os.path.basename(path)}")

    # --- Exit codes ---
    level = assessment.readiness_level
    if level == "READY":
        sys.exit(0)
    elif level == "CONDITIONAL":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
