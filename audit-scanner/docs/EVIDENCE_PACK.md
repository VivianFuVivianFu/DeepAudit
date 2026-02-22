# Evidence Pack Format (Deep-Audit)

This document describes the machine-readable evidence pack produced by Deep-Audit (`evidence_pack.py`). The pack is intentionally conservative: raw prompts and model responses are not included unless `STORE_RAW=true`.

Top-level fields
- `metadata`: run identifiers, timestamps, `config_snapshot`, and `config_hash` for reproducibility.
- `privacy`: whether raw data was stored and PII redaction stats.
- `scoring`: canonical single-source-of-truth scoring (`scoring_version`, `overall_score`, `confidence`).
- `cases`: array of detected failures; each case includes `case_id`, `category`, `severity`, `judge_confidence`, `evidence_refs`, and `safe_summary`.
- `safe_speed`: Safe-Speed layer heatmap with `layer`, `gap_score` (0-100), and `priority` (`low|medium|high`).
- `readiness_probe`: simple probes useful to determine audit readiness (coverage, consistent failures, etc.).
- `evidence_vault_index`: index entries mapping `evidence_id` to hashed summaries and location hints.

Reproducibility
- `metadata.config_snapshot` contains environment and runtime flags used for the run.
- `metadata.config_hash` is a SHA-256 hash of `config_snapshot` and should be stored alongside the report for verification.

Privacy
- By default `STORE_RAW=false`. To persist raw prompts and responses set `STORE_RAW=true` and configure secure storage (encrypted, TTL-backed) before enabling.

Extending the schema
- Additional fields may be added under `safe_speed` to include recommended remediation profiles and rollout plans.
