from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def main() -> int:
    parser = argparse.ArgumentParser(description="Show the parent AWS Batch job status")
    parser.add_argument("--manifest", type=Path, default=Path("deployment/last-run.json"))
    parser.add_argument("--profile")
    parser.add_argument("--region")
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        session_args: dict[str, str] = {}
        if args.profile:
            session_args["profile_name"] = args.profile
        if args.region or manifest.get("region"):
            session_args["region_name"] = args.region or manifest["region"]
        session = boto3.Session(**session_args)
        client = session.client(
            "batch",
            config=Config(
                retries={"total_max_attempts": 4, "mode": "adaptive"},
                connect_timeout=5,
                read_timeout=30,
            ),
        )
        response = client.describe_jobs(jobs=[manifest["job_id"]])
        if not response.get("jobs"):
            raise RuntimeError("Batch job was not found")
        job = response["jobs"][0]
        summary = {
            "jobId": job["jobId"],
            "jobName": job["jobName"],
            "status": job["status"],
            "statusReason": job.get("statusReason"),
            "arrayProperties": job.get("arrayProperties", {}),
            "resultsUri": manifest.get("results_uri"),
        }
        print(json.dumps(summary, indent=2))
        return 0
    except (BotoCoreError, ClientError, OSError, KeyError, RuntimeError, ValueError) as error:
        print(f"Status check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

