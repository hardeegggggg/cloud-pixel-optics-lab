from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.config import Config


def _s3_client():
    return boto3.client(
        "s3",
        config=Config(
            retries={"total_max_attempts": 4, "mode": "adaptive"},
            connect_timeout=5,
            read_timeout=30,
        ),
    )


def parse_s3_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.lstrip("/"):
        raise ValueError(f"Invalid S3 URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def read_text(location: str) -> str:
    if not location.startswith("s3://"):
        return Path(location).read_text(encoding="utf-8")
    bucket, key = parse_s3_uri(location)
    response = _s3_client().get_object(Bucket=bucket, Key=key)
    with response["Body"] as body:
        return body.read().decode("utf-8")


def write_json(value: dict, location: str) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True).encode("utf-8")
    if not location.startswith("s3://"):
        path = Path(location)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return

    bucket, key = parse_s3_uri(location)
    _s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=payload,
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )

