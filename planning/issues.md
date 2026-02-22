# Planning / Issues

NOTE: I attempted to locate `deep_audit_final_review_v2.md` and `deep_audit_safespeed_alignment.md` in the workspace but they were not found. Please provide their path or contents so I can extract the canonical blockers and Safe Speed mappings. Until then, the checklist below is derived from the session requirements and repo scan.

## Blockers Checklist (derived)
Each item includes acceptance criteria and initial code references.

1) Judge prompt-injection vulnerability / weak judge boundaries
- Acceptance criteria:
  - Judge prompt rewritten with conservative system directive.
  - Judge output validated against strict JSON schema (unit test).
  - Judge wrapped so agent responses cannot inject instructions (e.g., use explicit wrapper tags, truncated inputs).
  - Consistency check implemented (re-judge default N=2) and `judge_confidence` produced.
- Initial code refs: `audit-scanner/judge.py`, `audit-scanner/utils.py` (APIClient truncation), `audit-scanner/main.py` (judge invocation)

2) Failure category registry is hardcoded / wrong / not dynamic
- Acceptance criteria:
  - Categories defined by `AttackCase.category` registry, propagated to reports/scoring automatically.
  - Tests show adding a new `AttackCase` category updates reports without code edits.
- Initial code refs: `audit-scanner/attacks.py`, `audit-scanner/report_builder.py`, `audit-scanner/main.py`

3) Scoring logic duplicated / inconsistent
- Acceptance criteria:
  - Single source-of-truth `scoring.py` with `calculate_safety_score()` used by CLI, `run_full_assessment.py`, and report builder.
  - Unit tests for determinism and domain-level scoring.
- Initial code refs: `audit-scanner/main.py` ( `_calculate_safety_score` ), `audit-scanner/report_builder.py`, `audit-scanner/run_full_assessment.py`, `audit-scanner/SALES_FLOW_VERIFICATION.md` (references)

4) Fail-open behavior exists
- Acceptance criteria:
  - Any judge/client failure results in run marked `incomplete/low-confidence` and no silent pass.
  - Unit tests simulate judge failure and assert run state is 'incomplete' and not passing results.
- Initial code refs: `audit-scanner/judge.py` (note: current code returns "no failure detected" on judge exception), `audit-scanner/utils.py`

5) PII could leak to third-party judge/model APIs
- Acceptance criteria:
  - Redaction module implemented; PII removed before any remote API call.
  - Default config: `STORE_RAW=false`, `STORE_TTL_DAYS=0`.
  - Tests mock API client and assert PII patterns redacted.
- Initial code refs: `audit-scanner/utils.py` (APIClient.send_message), `audit-scanner/report_builder.py` (report contents)

6) Report leaks full attack prompts/responses (weaponization risk)
- Acceptance criteria:
  - Reports and evidence pack contain safe summaries and evidence_refs only; no full prompts/responses.
  - Evidence vault stores full artifacts only when `STORE_RAW=true` and encrypted/TTL-aware.
  - Snapshot test for report template to ensure full prompts absent.
- Initial code refs: `audit-scanner/report_builder.py`, `audit-scanner/REPORT_GUIDE.md` (mentions `audit_raw_*.json`)

7) Lack of reproducibility metadata
- Acceptance criteria:
  - Evidence pack and report include `config_hash`, `tool_version`, `model_versions`, `run_id`, timestamps and trace ids.
  - Tests verify presence and stability of `config_hash` for same config.
- Initial code refs: `audit-scanner/report_builder.py`, `audit-scanner/main.py` (entrypoint)

8) Missing tests for key modules
- Acceptance criteria:
  - Unit tests added for scoring, PII redaction, judge schema validation, category registry.
  - CI-friendly invocation via `pytest` (or similar).
- Initial code refs: `audit-scanner/tests/` (to be added), `audit-scanner/judge.py`, `audit-scanner/utils.py`, `audit-scanner/scoring.py` (to be added)

## Additional repo-sourced findings (from quick scan)
- `AttackCase` dataclass and `get_all_attack_cases()` exist (`attacks.py`).
- `APIClient` implemented in `utils.py`; it contains truncation and has a place to add redaction.
- `Judge` class implemented in `judge.py`. Current behavior: on exception, code returns a "safe default (no failure detected)" — this is fail-open (must change).
- Scoring logic appears in `main.py` as `_calculate_safety_score` and also referenced in `report_builder.py` and docs (`REPORT_GUIDE.md`, `SALES_FLOW_VERIFICATION.md`) — duplication risk.
- Report generator `report_builder.py` is comprehensive and already references Safe Speed, but report templates currently mention `audit_raw_*.json` for raw evidence (weaponization risk).
- Readiness tooling exists under `readiness/` with probes, engine, artifacts — a good starting point for Safe Speed mapping.
- No `Dockerfile` or `docker-compose.yml` detected in repo (none found in scan).

## Next Required Inputs
- Please provide `deep_audit_final_review_v2.md` and `deep_audit_safespeed_alignment.md` paths or paste their contents here so I can extract the canonical blocker list and Safe Speed mappings.

---

Generated by scan at: (automated)

