# Release Checklist

Use this checklist before releasing a new Deep-Audit version and publishing images.

1. Run tests

```bash
pip install -r audit-scanner/requirements.txt
python -m pytest audit-scanner/tests -q
```

2. Verify secrets are configured in GitHub (see `audit-scanner/docs/SECRETS.md`). Ensure:
- `RAW_STORAGE_KEY` or KMS/KeyVault secrets exist
- `GITHUB_TOKEN` has `packages: write` if publishing to GHCR
- For Docker Hub/ACR publishing: set the appropriate secrets

3. Build and run the image locally for smoke test

```bash
docker build -t deep-audit:local -f audit-scanner/Dockerfile .
docker run --rm -e ANTHROPIC_API_KEY=sk_xxx deep-audit:local --help
```

4. Tag and push release (GitHub release recommended). CI will publish images on `main`.

5. Post-release
- Rotate `RAW_STORAGE_KEY` if required and re-encrypt any persisted raw data using new key (or keep legacy keys until TTL expires).
- Monitor CI publish job logs and artifact uploads.
