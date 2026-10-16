from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def aggregate(input_dir: Path, output: Path) -> None:
    rows: list[dict] = []
    by_wavelength: dict[float, list[float]] = defaultdict(list)
    for path in sorted(input_dir.glob("wl*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        rows.append(row)
        by_wavelength[float(row["wavelength_nm"])].append(float(row["effective_response"]))

    if not rows:
        raise ValueError(f"No result JSON files found in {input_dir}")

    # ISSUE-003: arithmetic mean is wrong when angles/samples are not uniformly
    # spaced. A production metric needs trapezoidal or solid-angle weighting.
    mean_by_wavelength = {
        wavelength: sum(values) / len(values)
        for wavelength, values in by_wavelength.items()
    }
    for row in rows:
        row["unweighted_wavelength_mean"] = mean_by_wavelength[float(row["wavelength_nm"])]

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate local JSON results")
    parser.add_argument("--input-dir", type=Path, default=Path("output"))
    parser.add_argument("--output", type=Path, default=Path("output/aggregate.csv"))
    args = parser.parse_args()
    aggregate(args.input_dir, args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

