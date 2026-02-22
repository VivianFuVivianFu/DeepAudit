#!/usr/bin/env bash
# Helper: examples for setting GitHub repository secrets using `gh` CLI.
# Edit values or pipe in secure values in CI.

set -euo pipefail

echo "Setting RAW_STORAGE_KEY (example)"
RAW_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)

echo "$RAW_KEY" | gh secret set RAW_STORAGE_KEY --body -

echo "Set DOCKER_USERNAME and DOCKER_PASSWORD manually via prompts or CI secrets"
# gh secret set DOCKER_USERNAME --body "mydockeruser"
# gh secret set DOCKER_PASSWORD --body "$(cat ~/.docker/config.json)"

echo "Done. Verify in GitHub repository settings → Secrets and variables."
