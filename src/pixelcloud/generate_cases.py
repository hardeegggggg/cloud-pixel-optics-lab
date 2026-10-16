from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import PixelCase


def build_cases() -> list[PixelCase]:
    wavelengths = range(400, 701, 10)
    angles = range(0, 36, 5)
    decenters = (-0.10, -0.05, 0.0, 0.05, 0.10)
    cases: list[PixelCase] = []
    for wavelength_nm in wavelengths:
        for angle_deg in angles:
            for decenter_um in decenters:
                case_id = f"wl{wavelength_nm:03d}-a{angle_deg:02d}-d{decenter_um:+.2f}"
                cases.append(
                    PixelCase(
                        case_id=case_id,
                        wavelength_nm=float(wavelength_nm),
                        incident_angle_deg=float(angle_deg),
                        microlens_decenter_um=decenter_um,
                    )
                )
    return cases


def write_jsonl(cases: list[PixelCase], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(json.dumps(case.to_dict(), sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic pixel sweep cases")
    parser.add_argument("--output", type=Path, default=Path("data/cases.jsonl"))
    args = parser.parse_args()
    cases = build_cases()
    write_jsonl(cases, args.output)
    print(f"Wrote {len(cases)} cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

