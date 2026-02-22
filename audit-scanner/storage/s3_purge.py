import json
from datetime import datetime
from typing import List

import boto3


def list_meta_keys(bucket: str, prefix: str = "") -> List[str]:
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            k = obj["Key"]
            if k.endswith(".meta.json"):
                keys.append(k)
    return keys


def purge_expired_s3(bucket: str, prefix: str = "") -> List[str]:
    s3 = boto3.client("s3")
    removed = []
    keys = list_meta_keys(bucket, prefix)
    now = datetime.utcnow()
    for meta_key in keys:
        try:
            resp = s3.get_object(Bucket=bucket, Key=meta_key)
            meta = json.loads(resp["Body"].read())
            expires = meta.get("expires_at")
            enc_path = meta.get("encrypted_path")
            # encrypted_path may be a key or full path; derive S3 key for encrypted object
            enc_key = None
            if enc_path and enc_path.startswith("s3://"):
                # s3://bucket/key
                parts = enc_path[5:].split("/", 1)
                if len(parts) == 2:
                    enc_key = parts[1]
            else:
                # assume same prefix with .bin removed
                enc_key = meta_key.replace(".meta.json", ".bin")

            if expires:
                exp_dt = datetime.fromisoformat(expires)
                if exp_dt <= now:
                    # delete encrypted object if present
                    if enc_key:
                        try:
                            s3.delete_object(Bucket=bucket, Key=enc_key)
                            removed.append(f"s3://{bucket}/{enc_key}")
                        except Exception:
                            pass
                    # delete meta
                    s3.delete_object(Bucket=bucket, Key=meta_key)
                    removed.append(f"s3://{bucket}/{meta_key}")
        except Exception:
            continue
    return removed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Purge expired encrypted files from S3 bucket"
    )
    parser.add_argument("bucket", help="S3 bucket name")
    parser.add_argument("--prefix", default="", help="S3 prefix to scan")
    args = parser.parse_args()
    removed = purge_expired_s3(args.bucket, args.prefix)
    print(f"Removed {len(removed)} objects")
