#!/usr/bin/env python3
"""Estimate solid-model weight and filament length from a print-ready STL.

This is a solid-volume estimate (as if the part printed at 100% infill), not a
slicer replacement: real filament use depends on infill/wall settings this
script does not model. Use it for a rough upper bound, not a print-time quote.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_stl import load_stl, mesh_topology  # noqa: E402


def signed_volume(triangles) -> float:
    total = 0.0
    for a, b, c in triangles:
        cross = (
            b[1] * c[2] - b[2] * c[1],
            b[2] * c[0] - b[0] * c[2],
            b[0] * c[1] - b[1] * c[0],
        )
        total += a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]
    return abs(total) / 6.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stl", type=Path)
    parser.add_argument("--density", type=float, required=True, help="g/cm^3")
    parser.add_argument("--filament-diameter", type=float, default=1.75, help="mm")
    parser.add_argument("--tolerance", type=float, default=1e-4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    triangles, _encoding = load_stl(args.stl)
    non_manifold, flipped, components = mesh_topology(triangles, args.tolerance)

    warnings = []
    if non_manifold:
        warnings.append(f"{non_manifold} non-manifold edges: volume estimate may be unreliable")
    if flipped:
        warnings.append(f"{flipped} flipped-normal edges: volume estimate may be unreliable")

    volume_mm3 = signed_volume(triangles)
    volume_cm3 = volume_mm3 / 1000.0
    mass_g = volume_cm3 * args.density
    filament_area_mm2 = math.pi * (args.filament_diameter / 2) ** 2
    filament_length_mm = volume_mm3 / filament_area_mm2

    result = {
        "file": str(args.stl),
        "components": components,
        "volume_mm3": volume_mm3,
        "volume_cm3": volume_cm3,
        "density_g_cm3": args.density,
        "mass_g": mass_g,
        "filament_diameter_mm": args.filament_diameter,
        "filament_length_mm": filament_length_mm,
        "filament_length_m": filament_length_mm / 1000.0,
        "warnings": warnings,
        "note": "solid-model estimate (100% infill equivalent); actual print weight depends on slicer infill/wall settings",
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.stl}: {volume_cm3:.2f} cm^3 solid volume, {components} component(s)")
        print(f"estimated mass: {mass_g:.2f} g at {args.density} g/cm^3 (solid-model, not slicer-accurate)")
        print(f"estimated filament: {filament_length_mm / 1000.0:.2f} m at {args.filament_diameter} mm diameter")
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
