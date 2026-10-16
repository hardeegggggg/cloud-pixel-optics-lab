from __future__ import annotations

import argparse
from pathlib import Path

from .batch_runner import run_one
from .storage import read_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Run cases locally in serial")
    parser.add_argument("--cases", default="data/cases.jsonl")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    count = sum(1 for line in read_text(args.cases).splitlines() if line.strip())
    if args.limit is not None:
        if args.limit < 0:
            raise ValueError("Limit cannot be negative")
        count = min(count, args.limit)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    # ISSUE-005: deliberately serial. Replace with a bounded process pool and
    # keep per-case failures isolated instead of aborting the entire sweep.
    for index in range(count):
        destination = run_one(args.cases, index, output_dir=args.output_dir)
        print(f"[{index + 1}/{count}] {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

