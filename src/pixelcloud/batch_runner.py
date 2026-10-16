from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

from .models import PixelCase
from .simulator import simulate
from .storage import read_text, write_json


def load_case(cases_location: str, index: int) -> PixelCase:
    rows = [line for line in read_text(cases_location).splitlines() if line.strip()]
    # ISSUE-001: no explicit bounds check. An invalid Batch array size exposes a
    # low-context IndexError rather than a useful domain error.
    return PixelCase.from_dict(json.loads(rows[index]))


def result_location(case_id: str, output_dir: str | None, s3_prefix: str | None) -> str:
    # ISSUE-002: case_id alone means a rerun overwrites the prior result. Add a
    # run_id and a manifest while preserving idempotent retry behavior.
    filename = f"{case_id}.json"
    if s3_prefix:
        return f"{s3_prefix.rstrip('/')}/{filename}"
    return str(Path(output_dir or "output") / filename)


def run_one(
    cases_location: str,
    index: int,
    output_dir: str | None = None,
    s3_prefix: str | None = None,
) -> str:
    case = load_case(cases_location, index)
    result = simulate(case)
    destination = result_location(case.case_id, output_dir, s3_prefix)
    write_json(result.to_dict(), destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one pixel simulation case")
    parser.add_argument("--cases", default=os.getenv("CASES_S3_URI", "data/cases.jsonl"))
    parser.add_argument(
        "--index",
        type=int,
        default=int(os.getenv("AWS_BATCH_JOB_ARRAY_INDEX", "0")),
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--results-s3-prefix", default=os.getenv("RESULTS_S3_PREFIX"))
    args = parser.parse_args()

    try:
        destination = run_one(
            args.cases,
            args.index,
            output_dir=args.output_dir,
            s3_prefix=args.results_s3_prefix,
        )
        print(f"Wrote {destination}")
        return 0
    except (BotoCoreError, ClientError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Simulation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

