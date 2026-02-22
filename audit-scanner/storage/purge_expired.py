import os
import json
from datetime import datetime
from typing import List


def _find_meta_files(directory: str) -> List[str]:
    metas = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith(".meta.json"):
                metas.append(os.path.join(root, fname))
    return metas


def purge_expired(directory: str) -> List[str]:
    """Purge expired encrypted raw files based on .meta.json expiry

    Returns a list of removed file paths.
    """
    removed = []
    metas = _find_meta_files(directory)
    now = datetime.utcnow()
    for meta in metas:
        try:
            with open(meta, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            expires = data.get("expires_at")
            enc_path = data.get("encrypted_path")
            if expires:
                exp_dt = datetime.fromisoformat(expires)
                if exp_dt <= now:
                    # remove both encrypted file and meta file
                    try:
                        if enc_path and os.path.exists(enc_path):
                            os.remove(enc_path)
                            removed.append(enc_path)
                    except Exception:
                        pass
                    try:
                        os.remove(meta)
                        removed.append(meta)
                    except Exception:
                        pass
        except Exception:
            # ignore malformed meta
            continue

    return removed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Purge expired encrypted raw audit files"
    )
    parser.add_argument("directory", help="Directory to scan for encrypted metadata")
    args = parser.parse_args()

    removed = purge_expired(args.directory)
    print(f"Removed {len(removed)} files")
