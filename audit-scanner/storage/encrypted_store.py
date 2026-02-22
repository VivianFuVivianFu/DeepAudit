import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional

try:
    import boto3
except Exception:
    boto3 = None

try:
    # azure libs are optional
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
except Exception:
    DefaultAzureCredential = None
    SecretClient = None


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _get_key(env_var: str = "RAW_STORAGE_KEY") -> bytes:
    # Priority: direct env var -> KMS ciphertext -> Key Vault secret -> generate
    key = os.getenv(env_var)
    if key:
        return key.encode("utf-8") if isinstance(key, str) else key

    # AWS KMS encrypted key provided as base64 ciphertext in RAW_STORAGE_KEY_CIPHERTEXT
    kms_ct = os.getenv("RAW_STORAGE_KEY_CIPHERTEXT")
    if kms_ct and boto3:
        try:
            kms = boto3.client("kms")
            ct = base64.b64decode(kms_ct)
            resp = kms.decrypt(CiphertextBlob=ct)
            return resp["Plaintext"]
        except Exception:
            pass

    # Azure Key Vault secret name in RAW_STORAGE_KEY_VAULT_SECRET and vault URI in RAW_STORAGE_KEY_VAULT_URI
    vault_uri = os.getenv("RAW_STORAGE_KEY_VAULT_URI")
    vault_secret = os.getenv("RAW_STORAGE_KEY_VAULT_SECRET")
    if vault_uri and vault_secret and DefaultAzureCredential and SecretClient:
        try:
            cred = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_uri, credential=cred)
            sec = client.get_secret(vault_secret)
            val = sec.value
            return val.encode("utf-8") if isinstance(val, str) else val
        except Exception:
            pass

    # Fallback: generate a key (best-effort demo mode). Caller should prefer
    # providing a persistent key via env var or KMS for real deployments.
    generated = Fernet.generate_key()
    return generated


def store_raw_encrypted(
    data: Any,
    out_dir: str,
    filename_prefix: str = "audit_raw_enc",
    ttl_days: int = 0,
    key_env: str = "RAW_STORAGE_KEY",
) -> Dict[str, str]:
    """Encrypt and store raw audit data with a TTL metadata file.

    Returns dictionary with `encrypted_path` and `metadata_path`.
    """
    _ensure_dir(out_dir)

    key = _get_key(key_env)
    f = Fernet(key)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    enc_name = f"{filename_prefix}_{timestamp}.bin"
    enc_path = os.path.join(out_dir, enc_name)

    # Serialize data to JSON and encrypt
    payload = json.dumps(data, default=str).encode("utf-8")
    token = f.encrypt(payload)

    with open(enc_path, "wb") as fh:
        fh.write(token)

    # Metadata including TTL/expiry
    expires_at = None
    if ttl_days and int(ttl_days) > 0:
        expires_at = (datetime.utcnow() + timedelta(days=int(ttl_days))).isoformat()

    meta = {
        "encrypted_path": enc_path,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at,
        "key_env": key_env,
    }

    meta_path = enc_path + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    return {"encrypted_path": enc_path, "metadata_path": meta_path}


def load_raw_encrypted(enc_path: str, key_env: str = "RAW_STORAGE_KEY") -> Any:
    key = _get_key(key_env)
    f = Fernet(key)
    with open(enc_path, "rb") as fh:
        token = fh.read()
    payload = f.decrypt(token)
    return json.loads(payload.decode("utf-8"))
