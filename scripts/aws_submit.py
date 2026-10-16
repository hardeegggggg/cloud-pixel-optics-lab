from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


STACK_NAME = "PixelOpticsBatchStack"
SDK_CONFIG = Config(
    retries={"total_max_attempts": 4, "mode": "adaptive"},
    connect_timeout=5,
    read_timeout=30,
)


def create_session(profile: str | None, region: str | None) -> boto3.Session:
    kwargs: dict[str, str] = {}
    if profile:
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    return boto3.Session(**kwargs)


def stack_outputs(cloudformation, stack_name: str) -> dict[str, str]:
    response = cloudformation.describe_stacks(StackName=stack_name)
    stacks = response.get("Stacks", [])
    if len(stacks) != 1:
        raise RuntimeError(f"Expected one stack named {stack_name}")
    return {
        item["OutputKey"]: item["OutputValue"]
        for item in stacks[0].get("Outputs", [])
    }


def count_cases(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        count = sum(1 for line in handle if line.strip())
    if not 2 <= count <= 10_000:
        raise ValueError("AWS Batch array size must be between 2 and 10,000")
    return count


def safe_run_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", value).strip("-")
    if not cleaned:
        raise ValueError("Run ID must contain at least one letter or digit")
    return cleaned[:64]


def submit(
    cases_path: Path,
    run_id: str,
    stack_name: str,
    profile: str | None,
    region: str | None,
) -> dict:
    array_size = count_cases(cases_path)
    session = create_session(profile, region)
    cloudformation = session.client("cloudformation", config=SDK_CONFIG)
    s3 = session.client("s3", config=SDK_CONFIG)
    batch = session.client("batch", config=SDK_CONFIG)

    outputs = stack_outputs(cloudformation, stack_name)
    required = {"BucketName", "JobQueueArn", "JobDefinitionArn"}
    missing = sorted(required.difference(outputs))
    if missing:
        raise RuntimeError(f"Stack is missing outputs: {', '.join(missing)}")

    bucket = outputs["BucketName"]
    input_key = f"input/{run_id}/cases.jsonl"
    result_prefix = f"s3://{bucket}/results/{run_id}/"
    s3.upload_file(
        str(cases_path),
        bucket,
        input_key,
        ExtraArgs={
            "ContentType": "application/x-ndjson",
            "ServerSideEncryption": "AES256",
            "Metadata": {"run-id": run_id},
        },
    )

    response = batch.submit_job(
        jobName=f"pixel-optics-{run_id}"[:128],
        jobQueue=outputs["JobQueueArn"],
        jobDefinition=outputs["JobDefinitionArn"],
        arrayProperties={"size": array_size},
        containerOverrides={
            "environment": [
                {"name": "CASES_S3_URI", "value": f"s3://{bucket}/{input_key}"},
                {"name": "RESULTS_S3_PREFIX", "value": result_prefix},
                {"name": "PIXELCLOUD_RUN_ID", "value": run_id},
            ]
        },
        tags={"project": "cloud-pixel-optics", "run-id": run_id},
        propagateTags=True,
    )
    return {
        "job_id": response["jobId"],
        "job_name": response["jobName"],
        "array_size": array_size,
        "bucket": bucket,
        "input_uri": f"s3://{bucket}/{input_key}",
        "results_uri": result_prefix,
        "region": session.region_name,
        "run_id": run_id,
    }


def main() -> int:
    default_run_id = datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")
    parser = argparse.ArgumentParser(description="Upload cases and submit an AWS Batch array job")
    parser.add_argument("--cases", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--run-id", default=default_run_id)
    parser.add_argument("--stack-name", default=STACK_NAME)
    parser.add_argument("--profile")
    parser.add_argument("--region")
    parser.add_argument("--manifest", type=Path, default=Path("deployment/last-run.json"))
    args = parser.parse_args()

    try:
        run_id = safe_run_id(args.run_id)
        result = submit(args.cases, run_id, args.stack_name, args.profile, args.region)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (BotoCoreError, ClientError, OSError, RuntimeError, ValueError) as error:
        print(f"Submission failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

