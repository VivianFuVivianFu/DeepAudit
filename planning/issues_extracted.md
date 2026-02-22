# Planning / Issues (Extracted)

Files read for canonical blockers:

- c:\Users\vivia\Downloads\deep_audit_final_review_v2.md
- c:\Users\vivia\Downloads\deep_audit_safespeed_alignment.md

## Canonical Blockers (extracted from deep_audit_final_review_v2.md)

Each blocker below includes acceptance criteria and code references found in the repo.

B1 — Judge prompt-injection vulnerability (critical)
- Symptom: agent_response concatenated into judge prompt without system/user separation or safe wrapper (judge.py).
- Acceptance criteria:
  - System prompt moved to explicit system role; agent_response wrapped in a safe delimiter (e.g., <agent_response>..</agent_response>).
  - Judge JSON output validated by strict schema (unit test).
  - Unit test demonstrates that injection payloads in agent_response cannot alter judge outcome.
- Code refs: `audit-scanner/judge.py` (prompt construction / _parse_judge_response), `audit-scanner/utils.py` (APIClient send path)

B2 — PII forwarded to remote judge (critical)
- Symptom: raw target responses containing PII are sent to Anthropic/OpenAI without redaction.
- Acceptance criteria:
  - Implement redaction module removing email/phone/address/ID patterns before any remote call.
  - Default `STORE_RAW=false` and `STORE_TTL_DAYS=0` enforced; tests ensure no raw write on defaults.
  - When `STORE_RAW=true` require explicit opt-in and TTL + encrypted storage behavior documented.
- Code refs: `audit-scanner/utils.py` (APIClient.send_message), `audit-scanner/report_builder.py` (evidence output)

B3 — Failure category enum outdated / hardcoded
- Symptom: code restricts categories to an old set (5) while attacks include 9 categories, causing misclassification.
- Acceptance criteria:
  - Categories derived dynamically from `AttackCase.category` values; registry API available.
  - Tests show adding a new AttackCase category auto-propagates to reports/scoring.
- Code refs: `audit-scanner/attacks.py`, `audit-scanner/report_builder.py`, `audit-scanner/judge.py`

B4 — Fail-open behavior and exit/threshold inconsistency
- Symptom: on judge/API errors code returns a safe-default (no failure) or gateways fall-back to pass-through (safe_speed_adapter.py), and `--fail_threshold` logic is inconsistent.
- Acceptance criteria:
  - On judge failure mark run "incomplete/low-confidence"; do not silently pass failures.
  - Add `--strict` option to explicitly fail CI when desired; default behavior marks run incomplete.
  - Tests that simulate judge outage assert run state and propagate proper exit codes when `--strict` set.
- Code refs: `audit-scanner/judge.py`, `audit-scanner/main.py`, `audit-scanner/safe_speed_adapter.py`

B5 — Accumulation bug: repeated runs append prior results
- Acceptance criteria:
  - `AuditScanner.run_audit()` resets internal evaluation lists at start; unit test ensures idempotence over repeated runs.
- Code refs: `audit-scanner/main.py` (AuditScanner implementation)

B6 — Scoring duplicated across modules (SSoT missing)
- Symptom: scoring logic implemented in `main.py`, `report_builder.py`, `pdf_report.py`, `demo_flow.py` with inconsistent thresholds.
- Acceptance criteria:
  - Create `audit-scanner/scoring.py` with single `calculate_safety_score()` used everywhere.
  - Unit tests for determinism; same inputs -> same score; domain-level scores included in evidence pack.
- Code refs: `audit-scanner/main.py`, `audit-scanner/report_builder.py`, `audit-scanner/pdf_report.py`, `audit-scanner/demo/demo_flow.py`

B7 — Severity / critical definition inconsistent
- Acceptance criteria:
  - Canonical severity mapping documented and used consistently; tests asserting executive_summary vs key_findings alignment.
- Code refs: `audit-scanner/report_builder.py` (executive summary, key_findings)

B8 — health_check implementation brittle
- Acceptance criteria:
  - Health checks use appropriate preset "hello" payloads per provider; do not rely on GET /
  - Tests for health_check against mock presets.
- Code refs: `audit-scanner/utils.py` (health_check)

B9 — example_report.md is stale and internally inconsistent
- Acceptance criteria:
  - Regenerate `example_report.md` from `report_builder.py` using sample run; replace manual file.
  - Snapshot test to prevent drift.
- Code refs: `audit-scanner/report_builder.py`, `example_report.md`

B10 — safe_speed_adapter fail-open
- Acceptance criteria:
  - On gateway unavailability adapter must fail-closed (mark blocked or low-confidence), not return raw responses.
  - Tests simulate gateway down and assert no unmediated output is returned.
- Code refs: `audit-scanner/demo/safe_speed_adapter.py`

B11 — Reports expose full attack prompts (weaponization)
- Acceptance criteria:
  - Report evidence sections must contain only safe summaries + evidence_ids; raw prompts/responses only stored in evidence vault when `STORE_RAW=true`.
  - Appendix redaction enforced; unit tests / snapshot tests validate no raw prompts in human report.
- Code refs: `audit-scanner/report_builder.py`, `audit-scanner/REPORT_GUIDE.md`

B12 — Duplicate validators (validate.py vs validate_full_system.py)
- Acceptance criteria:
  - Consolidate to single validator (`validate_full_system.py`) and update docs; tests to confirm parity.
- Code refs: `audit-scanner/validate.py`, `audit-scanner/validate_full_system.py`

B13 — v1 docs coexist with v2 (confusing)
- Acceptance criteria:
  - Archive or tag v1 docs; canonical docs point to v2 (SUMMARY.md/demo/README.md). Update landing page copy.
- Code refs: `PROJECT_INDEX.md`, `QUICKSTART.md`, `ARCHITECTURE.md`, front-end `audit-landing/app/page.tsx`

B14 — SignalExtractor inefficiency in engine.py
- Acceptance criteria:
  - Cache extraction results; tests for performance/regression.
- Code refs: `audit-scanner/readiness/engine.py` ( _recommended_profile_label )

B15 — landing page outdated attack list
- Acceptance criteria:
  - Update `page.tsx` content to list 9 attack categories and link to v2 docs.
- Code refs: `audit-landing/app/page.tsx`

## Safe Speed alignment (extracted from deep_audit_safespeed_alignment.md)

- Current coverage: Layer 3 mostly covered (~70%), Layer 1 (observability/drift) weak (~15%), Layer 2 partial (~25%), Layer 4 minimal (~5%).
- Key prescriptions from that doc (accepted as source-of-truth):
  - Add `safe_speed_layer` mapping per failure and heatmap in reports.
  - Readiness Assessment must output `recommended_safe_speed_profile` and a 90-day rollout plan.
  - Add Docker one-line startup, local-judge option, and PII guarantees (local judge default for enterprise).

## Acceptance criteria summary (high-level)

- Judge hardening: schema validation, wrapper tags, re-judge consistency (N=2 default), unit tests for injection resistance.
- PII redaction: regex + light NER before any remote call; default store disabled; opt-in encrypted TTL storage.
- Categories: dynamic registry from `AttackCase.category`.
- Scoring SSoT: new `scoring.py` used by CLI, reports, pdf, demos; deterministic tests.
- Fail-safe: judge/gateway failures must mark run incomplete and avoid silent pass.
- Evidence pack: JSON per required schema with metadata, privacy, scoring, cases, safe_speed, readiness_probe, evidence_vault_index.

## Next steps (Phase 1 immediate edits)

1) Implement `audit-scanner/privacy/redactor.py` and integrate into `APIClient.send_message()`.
2) Create `audit-scanner/scoring.py` and migrate scoring calls; add unit tests `tests/test_scoring.py`.
3) Harden `audit-scanner/judge.py`: system prompt, wrapper tags, schema validation, re-judge consistency; add `tests/test_judge_schema.py`.
4) Change fail-open behavior: `judge.py` and `safe_speed_adapter.py` to mark run `incomplete/low-confidence` on failures; add tests.
5) Update `planning/issues.md` with canonical blockers (this file).

Once you confirm, I'll apply edits in that order and run unit tests after each change, reporting diffs and results.
