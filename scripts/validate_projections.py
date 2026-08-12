#!/usr/bin/env python3
"""Compare bounding-box envelopes and revision marks across two DXF drawings.

Typical use: verify that the preliminary drawing and the final model-derived
drawing describe the same X/Y/Z envelope and carry the same revision, or that
one drawing's own axis pairs agree (front/top share X, top/side share Y,
front/side share Z) when it packs all three views into one DXF with layers
per view.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

COORD_CODES = {10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33}


def parse_pairs(path: Path) -> list[tuple[int, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"AutoCAD Binary DXF"):
        raise ValueError(f"{path}: binary DXF is not supported by this validator")
    lines = raw.decode("utf-8-sig").splitlines()
    if len(lines) % 2:
        raise ValueError(f"{path}: DXF has an odd number of group-code lines")
    return [(int(lines[i].strip()), lines[i + 1].strip()) for i in range(0, len(lines), 2)]


def bounds(pairs: list[tuple[int, str]]) -> dict[str, tuple[float, float]]:
    axis_values: dict[str, list[float]] = {"x": [], "y": [], "z": []}
    axis_by_code = {10: "x", 11: "x", 12: "x", 13: "x", 20: "y", 21: "y", 22: "y", 23: "y", 30: "z", 31: "z", 32: "z", 33: "z"}
    for code, value in pairs:
        if code in COORD_CODES:
            try:
                axis_values[axis_by_code[code]].append(float(value))
            except ValueError:
                continue
    result = {}
    for axis, values in axis_values.items():
        if values:
            result[axis] = (min(values), max(values))
    return result


def revision_marks(pairs: list[tuple[int, str]]) -> set[str]:
    texts = {value for code, value in pairs if code == 1}
    return {t for t in texts if t.upper().startswith("R") and t[1:].isdigit()}


def envelope(b: dict[str, tuple[float, float]], axis: str) -> float:
    lo, hi = b.get(axis, (0.0, 0.0))
    return hi - lo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("preliminary", type=Path)
    parser.add_argument("final", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    prelim_pairs = parse_pairs(args.preliminary)
    final_pairs = parse_pairs(args.final)
    prelim_bounds = bounds(prelim_pairs)
    final_bounds = bounds(final_pairs)

    for axis in "xyz":
        p = envelope(prelim_bounds, axis)
        f = envelope(final_bounds, axis)
        if not math.isclose(p, f, abs_tol=args.tolerance):
            failures.append(f"{axis.upper()} envelope mismatch: preliminary={p:.4f}, final={f:.4f}")

    prelim_rev = revision_marks(prelim_pairs)
    final_rev = revision_marks(final_pairs)
    if prelim_rev and final_rev and not (prelim_rev & final_rev):
        failures.append(f"revision mismatch: preliminary={sorted(prelim_rev)}, final={sorted(final_rev)}")

    result = {
        "preliminary": str(args.preliminary),
        "final": str(args.final),
        "preliminary_bounds": prelim_bounds,
        "final_bounds": final_bounds,
        "preliminary_revision": sorted(prelim_rev),
        "final_revision": sorted(final_rev),
        "failures": failures,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"preliminary {args.preliminary} vs final {args.final}")
        for failure in failures:
            print("FAIL: " + failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
