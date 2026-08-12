#!/usr/bin/env python3
"""Validate structural and workflow invariants of an ASCII engineering DXF."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def parse_pairs(path: Path) -> list[tuple[int, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"AutoCAD Binary DXF"):
        raise ValueError("binary DXF is not supported by this validator")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    if len(lines) % 2:
        raise ValueError("DXF has an odd number of group-code lines")
    pairs = []
    for index in range(0, len(lines), 2):
        try:
            code = int(lines[index].strip())
        except ValueError as exc:
            raise ValueError(f"invalid group code at line {index + 1}") from exc
        pairs.append((code, lines[index + 1].strip()))
    return pairs


def value_after(pairs: list[tuple[int, str]], marker: str, code: int) -> str | None:
    for index, pair in enumerate(pairs[:-1]):
        if pair == (9, marker) and pairs[index + 1][0] == code:
            return pairs[index + 1][1]
    return None


def entity_records(pairs: list[tuple[int, str]]) -> list[tuple[str, list[tuple[int, str]]]]:
    inside = False
    current_kind: str | None = None
    current: list[tuple[int, str]] = []
    records = []
    for code, value in pairs:
        if (code, value) == (2, "ENTITIES"):
            inside = True
            continue
        if not inside:
            continue
        if code == 0:
            if current_kind:
                records.append((current_kind, current))
            if value == "ENDSEC":
                return records
            current_kind, current = value, []
        else:
            current.append((code, value))
    return records


def first(data: list[tuple[int, str]], code: int) -> str | None:
    return next((value for item_code, value in data if item_code == code), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf", type=Path)
    parser.add_argument("--expect-layer", action="append", default=[])
    parser.add_argument("--expect-text", action="append", default=[])
    parser.add_argument("--min-geometry", type=int, default=1)
    parser.add_argument("--allow-non-mm", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    try:
        pairs = parse_pairs(args.dxf)
    except (OSError, UnicodeError, ValueError) as exc:
        failures.append(str(exc))
        pairs = []

    records = entity_records(pairs) if pairs else []
    counts = Counter(kind for kind, _ in records)
    geometry_types = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE"}
    geometry_count = sum(counts[kind] for kind in geometry_types)
    entity_layers = {first(data, 8) for _, data in records}
    declared_layers = {value for index, (code, value) in enumerate(pairs) if code == 2 and index > 0 and pairs[index - 1] == (0, "LAYER")}
    layers = {layer for layer in entity_layers | declared_layers if layer}
    texts = [first(data, 1) or "" for kind, data in records if kind in {"TEXT", "MTEXT"}]
    units = value_after(pairs, "$INSUNITS", 70)

    if not pairs or pairs[-1] != (0, "EOF"):
        failures.append("missing final EOF terminator")
    if not args.allow_non_mm and units != "4":
        failures.append(f"$INSUNITS must be 4 (millimetres), found {units!r}")
    if geometry_count < args.min_geometry:
        failures.append(f"editable geometry count {geometry_count} is below {args.min_geometry}")
    for layer in args.expect_layer:
        if layer not in layers:
            failures.append(f"missing expected layer: {layer}")
    joined_text = "\n".join(texts).casefold()
    for expected in args.expect_text:
        if expected.casefold() not in joined_text:
            failures.append(f"missing expected text: {expected}")

    finite_coordinates = True
    for _, data in records:
        for code, value in data:
            if code in {10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33, 40, 41, 42}:
                try:
                    finite_coordinates = finite_coordinates and math.isfinite(float(value))
                except ValueError:
                    failures.append(f"non-numeric coordinate/value: {value!r}")
                    finite_coordinates = False
    if not finite_coordinates:
        failures.append("DXF contains non-finite or invalid numeric geometry")

    result = {
        "file": str(args.dxf),
        "units": "mm" if units == "4" else units,
        "layers": sorted(layers),
        "entities": dict(sorted(counts.items())),
        "editable_geometry": geometry_count,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{args.dxf}: {geometry_count} editable geometry entities; units={result['units']}")
        print("layers: " + ", ".join(result["layers"]))
        if failures:
            for failure in failures:
                print("FAIL: " + failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
