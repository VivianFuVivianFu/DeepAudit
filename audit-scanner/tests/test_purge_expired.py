import os
import json
from datetime import datetime, timedelta

from storage.purge_expired import purge_expired


def test_purge_expired(tmp_path):
    # create fake encrypted file and meta with past expiry
    enc = tmp_path / "audit_raw_enc_000.bin"
    enc.write_bytes(b"xxx")

    meta = tmp_path / "audit_raw_enc_000.bin.meta.json"
    past = (datetime.utcnow() - timedelta(days=2)).isoformat()
    meta.write_text(json.dumps({"encrypted_path": str(enc), "expires_at": past}))

    removed = purge_expired(str(tmp_path))
    assert any(str(enc) in r for r in removed)
    assert any(str(meta) in r for r in removed)
