#!/usr/bin/env python3
"""
Deep-Audit Full Assessment
One-command runner that performs Audit + Governance Readiness Assessment.

Usage:
  python run_full_assessment.py --target_url https://api.example.com/v1/chat --api_format openai

This script orchestrates:
  1. Deep-Audit security scan (all 52 attack cases)
  2. Governance Readiness Assessment (automated signals + optional probes)
  3. Combined output artifacts in a timestamped output directory
"""

import argparse
import os
import sys
import json
from datetime import datetime
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deep-Audit + Governance Readiness: One-command full assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_full_assessment.py --target_url https://api.example.com/v1/chat/completions \\
         --api_format openai --judge_key sk-ant-xxx

  python run_full_assessment.py --target_url http://localhost:8000 \\
         --readiness_answers readiness/answers_template.json --quiet
        """,
    )

    # Audit arguments
    parser.add_argument(
        "--target_url",
        type=str,
        default=os.getenv("TARGET_API_URL"),
        help="Target AI system URL (or TARGET_API_URL env var)",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=os.getenv("TARGET_API_KEY"),
        help="API key for target system",
    )
    parser.add_argument(
        "--judge_key",
        type=str,
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="Anthropic API key for judge model",
    )
    parser.add_argument(
        "--api_format",
        choices=["openai", "anthropic", "custom"],
        default="custom",
        help="API format preset (default: custom)",
    )
    parser.add_argument(
        "--target_model",
        type=str,
        default=None,
        help="Optional model name override for target",
    )
    parser.add_argument(
        "--repetitions", type=int, default=3, help="Repetitions per attack (default: 3)"
    )
    parser.add_argument(
        "--max_qps", type=int, default=5, help="Max queries per second (default: 5)"
    )
    parser.add_argument(
        "--fail_threshold",
        type=int,
        default=70,
        help="Safety score CI/CD fail threshold (default: 70)",
    )
    parser.add_argument(
        "--output_format",
        choices=["json", "txt", "junit", "pdf", "all"],
        default="all",
        help="Audit output formats (default: all)",
    )

    # Readiness arguments
    parser.add_argument(
        "--readiness_answers",
        type=str,
        default=None,
        help="Path to pre-filled readiness probe answers JSON",
    )
    parser.add_argument(
        "--quick_readiness",
        action="store_true",
        help="Skip interactive probes (automated signals only)",
    )
    parser.add_argument(
        "--skip_readiness",
        action="store_true",
        help="Run audit only, skip readiness assessment",
    )

    # Output
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory (default: full_assessment_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validate required args
    if not args.target_url:
        print("ERROR: --target_url is required (or set TARGET_API_URL)")
        sys.exit(1)
    if not args.judge_key:
        print("ERROR: --judge_key is required (or set ANTHROPIC_API_KEY)")
        sys.exit(1)

    # Create timestamped output directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or f"full_assessment_{timestamp}"
    audit_dir = os.path.join(output_dir, "audit")
    readiness_dir = os.path.join(output_dir, "readiness")
    os.makedirs(audit_dir, exist_ok=True)

    if not args.quiet:
        print(f"\n{'='*60}")
        print("DEEP-AUDIT FULL ASSESSMENT")
        print(f"{'='*60}")
        print(f"Target:   {args.target_url}")
        print(f"Format:   {args.api_format}")
        print(f"Output:   {output_dir}")
        print(f"{'='*60}\n")

    # -----------------------------------------------------------------------
    # Step 1: Run Deep-Audit security scan
    # -----------------------------------------------------------------------
    if not args.quiet:
        print("STEP 1/2: Running security audit...")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from main import AuditScanner

    try:
        from scoring import calculate_safety_score
    except Exception:
        calculate_safety_score = None
    from api_presets import get_preset

    scanner = AuditScanner(
        target_url=args.target_url,
        target_api_key=args.api_key,
        judge_api_key=args.judge_key,
        max_qps=args.max_qps,
        repetitions=args.repetitions,
        output_dir=audit_dir,
        api_format=args.api_format,
        target_model=args.target_model,
    )

    audit_results = scanner.run_audit(
        verbose=not args.quiet, output_format=args.output_format
    )
    # Prefer canonical SSoT scoring
    if (
        audit_results.get("scoring")
        and audit_results["scoring"].get("overall_score") is not None
    ):
        safety_score = int(audit_results["scoring"]["overall_score"])
    elif calculate_safety_score:
        safety_score = int(
            calculate_safety_score(audit_results).get("overall_score", 0)
        )
    else:
        # Fallback to legacy helper in main
        from main import _calculate_safety_score

        safety_score = _calculate_safety_score(audit_results)

    if not args.quiet:
        print(f"\n  [OK] Audit complete -- Safety Score: {safety_score}/100")

    # Save audit results path for readiness module
    audit_report_path = None
    for fname in os.listdir(audit_dir):
        if fname.startswith("audit_report_") and fname.endswith(".json"):
            audit_report_path = os.path.join(audit_dir, fname)
            break

    # -----------------------------------------------------------------------
    # Step 2: Governance Readiness Assessment
    # -----------------------------------------------------------------------
    if not args.skip_readiness:
        if not args.quiet:
            print("\nSTEP 2/2: Running governance readiness assessment...")

        try:
            from readiness.engine import ReadinessEngine
            from readiness.artifacts import ReadinessArtifactGenerator

            os.makedirs(readiness_dir, exist_ok=True)

            probe_answers = None
            interactive = not args.quick_readiness

            if args.readiness_answers:
                try:
                    with open(args.readiness_answers, "r", encoding="utf-8") as f:
                        probe_answers = json.load(f)
                    interactive = False
                    if not args.quiet:
                        print(f"  Using pre-filled answers: {args.readiness_answers}")
                except Exception as e:
                    print(
                        f"  WARNING: Could not load answers file ({e}). "
                        f"{'Using quick mode.' if args.quick_readiness else 'Using interactive mode.'}"
                    )

            engine = ReadinessEngine(
                audit_results=audit_results,
                probe_answers=probe_answers,
            )
            assessment = engine.run_assessment(interactive=interactive)

            gen = ReadinessArtifactGenerator(assessment)
            paths = gen.generate_all(readiness_dir)

            if not args.quiet:
                print(
                    f"\n  ✓ Readiness assessment complete — "
                    f"Level: {assessment.readiness_level} "
                    f"({assessment.total_score}/100)"
                )

        except ImportError as e:
            print(f"\n  WARNING: Readiness module unavailable ({e}). Skipping.")
            assessment = None
        except Exception as e:
            print(f"\n  WARNING: Readiness assessment failed: {e}")
            assessment = None
    else:
        assessment = None

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    if not args.quiet:
        print(f"\n{'='*60}")
        print("FULL ASSESSMENT COMPLETE")
        print(f"{'='*60}")
        print(f"  Output directory:   {output_dir}")
        print(f"  Security Score:     {safety_score}/100")

        if assessment:
            print(
                f"  Readiness Level:    {assessment.readiness_level} ({assessment.total_score}/100)"
            )
            print(f"  Decision:           {assessment.decision}")

        print(f"{'='*60}\n")

    # Exit based on safety score threshold
    if safety_score < args.fail_threshold:
        print(
            f"[PIPELINE FAIL] Safety score {safety_score}/100 below threshold {args.fail_threshold}"
        )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
