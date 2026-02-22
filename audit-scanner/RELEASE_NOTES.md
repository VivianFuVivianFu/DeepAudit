# Release Notes — Deep Audit Enterprise Upgrade

Date: 2026-02-22

Summary
-------
- Upgraded `audit-scanner` to enterprise audit-grade behavior: PII redaction, judge hardening (re-judge + confidence), SSoT scoring, evidence pack export, encrypted raw storage with TTL, purge helpers (local & S3), and CI/Docker publishing scaffolding.

Validation
----------
- Unit tests: 9 passed, 2 skipped, 6 warnings (ran with `pytest -q`).
- Integration smoke test: 1 skipped (monkeypatched). See `tests/test_integration_smoke.py` for details.
- Lint/format: ran `ruff` and `black` in the project venv; `black` auto-formatted code where necessary.
- Docker image build: attempted `docker build -t deep-audit .` but Docker Engine was not available on the host (start Docker Desktop or Docker Engine and re-run the command).

Notable Files Changed / Added
----------------------------
- `privacy/redactor.py` — PII redaction helper used across the pipeline.
- `scoring.py` — SSoT safety scoring functions.
- `evidence_pack.py` — Evidence pack exporter (metadata, config hash, heatmap, readiness probe).
- `storage/encrypted_store.py` — Fernet-based encrypted raw storage with optional KMS/KeyVault support and TTL metadata.
- `storage/purge_expired.py` / `storage/s3_purge.py` — Purge helpers for expired artifacts.
- `RELEASE_NOTES.md` — this file.

Next Steps / Recommendations
---------------------------
- Start Docker Desktop (or ensure Docker Engine is running) and run:

```powershell
Set-Location -Path 'C:\Users\vivia\OneDrive\Desktop\Deep Audit\audit-scanner'
docker build -t deep-audit .
```

- Provision CI secrets for publishing and purge jobs (AWS credentials or Azure Key Vault + registry credentials). See `docs/SECRETS.md`.
- Optionally enable scheduled purge workflows in GitHub Actions once remote storage credentials are configured.

Contact
-------
If you'd like, I can:
- run the Docker build after you start Docker on this machine,
- push the image to a registry (requires credentials),
- add an automated key-rotation helper for the encrypted store.
