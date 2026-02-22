import os
import pytest


def test_store_and_load_encrypted(tmp_path, monkeypatch):
    pytest.importorskip("cryptography")
    from storage.encrypted_store import store_raw_encrypted, load_raw_encrypted
    from cryptography.fernet import Fernet

    # Provide a deterministic key via env
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("RAW_STORAGE_KEY", key)

    data = {"foo": "bar", "n": 1}
    out = store_raw_encrypted(data, str(tmp_path), ttl_days=1)
    enc_path = out["encrypted_path"]
    meta_path = out["metadata_path"]

    assert os.path.exists(enc_path)
    assert os.path.exists(meta_path)

    loaded = load_raw_encrypted(enc_path)
    assert loaded["foo"] == "bar"
    assert loaded["n"] == 1
