#!/usr/bin/env python3
"""Perform structural checks on an ASCII STEP file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=Path)
    parser.add_argument("--expect-product", action="append", default=[])
    parser.add_argument("--min-solids", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = args.step.read_text(encoding="utf-8", errors="strict")
    entities = len(re.findall(r"^#\d+\s*=", text, re.MULTILINE))
    solids = text.count("MANIFOLD_SOLID_BREP")
    products = re.findall(r"PRODUCT\('([^']*)'", text)
    failures = []
    if not text.lstrip().startswith("ISO-10303-21;"):
        failures.append("missing STEP header")
    if not text.rstrip().endswith("END-ISO-10303-21;"):
        failures.append("missing STEP terminator")
    if entities == 0:
        failures.append("no STEP entities")
    if solids < args.min_solids:
        failures.append(f"BREP solids {solids} < {args.min_solids}")
    for expected in args.expect_product:
        if expected not in products and expected not in text:
            failures.append(f"missing product/component name: {expected}")

    result = {
        "file": str(args.step),
        "entities": entities,
        "brep_solids": solids,
        "products": products,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.step}: {entities} entities, {solids} BREP solids")
        print("products:", ", ".join(products) if products else "(none)")
        for failure in failures:
            print(f"FAIL: {failure}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
