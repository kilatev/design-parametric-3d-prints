#!/usr/bin/env python3
"""Validate a delivery manifest.json: required fields, file presence, revision match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_TOP_LEVEL = ("revision", "units", "approved_drawing", "files")
REQUIRED_FILES = ("source", "step", "stl")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expect-revision")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: could not read manifest: {exc}")
    base = args.manifest.parent.resolve()

    def resolve_within_base(relative: str) -> Path | None:
        candidate = (base / relative).resolve()
        if not candidate.is_relative_to(base):
            return None
        return candidate

    for field in REQUIRED_TOP_LEVEL:
        if field not in manifest:
            failures.append(f"missing required field: {field}")

    files = manifest.get("files", {})
    for key in REQUIRED_FILES:
        if key not in files:
            failures.append(f"files.{key} is missing from manifest")
            continue
        path = resolve_within_base(files[key])
        if path is None:
            failures.append(f"files.{key} escapes manifest directory: {files[key]}")
        elif not path.exists():
            failures.append(f"files.{key} does not exist: {path}")

    approved = manifest.get("approved_drawing")
    if approved:
        approved_path = resolve_within_base(approved)
        if approved_path is None:
            failures.append(f"approved_drawing escapes manifest directory: {approved}")
        elif not approved_path.exists():
            failures.append(f"approved_drawing does not exist: {approved_path}")

    if args.expect_revision and manifest.get("revision") != args.expect_revision:
        failures.append(f"revision {manifest.get('revision')!r} does not match expected {args.expect_revision!r}")

    result = {"file": str(args.manifest), "manifest": manifest, "failures": failures}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.manifest}: revision={manifest.get('revision')}")
        for failure in failures:
            print("FAIL: " + failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
