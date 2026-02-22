# CI & Registry Secrets

This document lists the secrets used by the GitHub Actions workflow `docker_build_and_publish.yml` and how to provision them for enterprise publishing and scheduled purge automation.

Recommended secrets (set in GitHub repository `Settings → Secrets → Actions`):

- `GHCR_TOKEN` — Personal access token with `read:packages`, `write:packages`, and `workflow` scopes for pushing to GitHub Container Registry (ghcr.io). If set, the CI will push to GHCR as `ghcr.io/<org>/deep-audit:latest`.

- `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` — Docker Hub username and access token (or password). If set, the CI will attempt to push image to DockerHub under `<username>/deep-audit:latest`.

- `ACR_LOGIN_SERVER` / `ACR_USERNAME` / `ACR_PASSWORD` — For Azure Container Registry (e.g., `myregistry.azurecr.io`). If set, the CI will push image to ACR.

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — Required when running S3 purge workflows that interact with AWS S3.

- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` — Required for Azure Key Vault integrations and any ACR interactions that rely on service principal authentication.

Notes:
- The workflow will detect which registries to push to based on which secrets are present. You only need to set the secrets for the registries you use.
- For maximum safety, create scoped service accounts or machine principals with least privilege for publish and purge operations.

How to trigger the workflow manually (without `gh`):
1. Create a Personal Access Token with `repo` and `workflow` permissions in GitHub.
2. From a machine with PowerShell, run:

```powershell
$env:GITHUB_TOKEN = '<PERSONAL_ACCESS_TOKEN>'
.\scripts\trigger_workflow.ps1 -Repo 'owner/repo' -WorkflowFile 'docker_build_and_publish.yml' -Ref 'main'
```

Or trigger from the GitHub UI: `Actions` → choose `Build and Publish Docker Image` → `Run workflow`.
# Secrets and CI credentials guide

This guide explains required repository secrets and recommended practices for configuring CI and encrypted raw storage securely.

Required secrets (used by workflows in this repo)

- `GITHUB_TOKEN` (provided by Actions automatically). Ensure repository `Actions` settings allow `GITHUB_TOKEN` to have `packages: write` if you want GHCR publish.
- `RAW_STORAGE_KEY` — symmetric Fernet key used to encrypt raw audit files. Generate with:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

Store the resulting key as `RAW_STORAGE_KEY` in repository secrets (or organization secrets for multiple repos).

Optional secrets for CI publishing and purge workflows

- `DOCKER_USERNAME` / `DOCKER_PASSWORD` — for Docker Hub publishing.
- `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD` — for Azure Container Registry publishing.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` — for S3 purge workflow.
- `S3_PURGE_BUCKET` / `S3_PURGE_PREFIX` — bucket and prefix to scan for `.meta.json` metadata.
- `PURGE_DIR` — local path for scheduled purge workflow (used by self-hosted runner scenario).

Setting secrets via GitHub web UI

1. Go to your repository → Settings → Secrets and variables → Actions → New repository secret.
2. Add the secret name and value, then save.

Setting secrets via GitHub CLI

Make sure you have `gh` installed and authenticated.

```bash
# Example: set RAW_STORAGE_KEY
gh secret set RAW_STORAGE_KEY --body "$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)"

# Docker Hub credentials
gh secret set DOCKER_USERNAME --body "mydockeruser"
gh secret set DOCKER_PASSWORD --body "$(cat ~/.docker/config.json | jq -r .auths)"
```

Notes and best practices

- Prefer organization-level secrets for production CI pipelines and restrict repository access.
- Use a cloud KMS (AWS KMS, Azure Key Vault, Google KMS) to manage the `RAW_STORAGE_KEY` in production; store only a KMS-wrapped key in GitHub Secrets when needed.
- Rotate `RAW_STORAGE_KEY` periodically and maintain key-rotation records. When rotating, re-encrypt persisted raw files or mark previous encrypted artifacts as legacy and retain them until their TTL expires.
- Limit who can read or change secrets: GitHub supports environment-based secrets with deployment protection.
- For GHCR publishing ensure `GITHUB_TOKEN` has `packages: write` enabled in repository settings or configure a personal access token (PAT) with `write:packages` scope and store as `GHCR_PAT`.

Troubleshooting

- If CI publish fails with permission errors, check repository Actions settings and whether `GITHUB_TOKEN` has the `packages: write` scope enabled.
- For S3 purge workflows, run the purge locally first with AWS credentials configured in your environment to validate behavior:

```bash
python audit-scanner/storage/s3_purge.py my-bucket --prefix "deep-audit/raw"
```
