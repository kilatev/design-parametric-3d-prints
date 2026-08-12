#!/usr/bin/env python3
"""Diff two revisions of parameters.json: added, removed, and changed values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SECTIONS = ("nominal", "clearances", "derived")


def flatten(doc: dict) -> dict:
    flat = {k: doc[k] for k in ("revision", "units") if k in doc}
    flat |= {f"{s}.{k}": v for s in SECTIONS for k, v in doc.get(s, {}).items()}
    flat |= {f"instances.{i.get('name', '?')}": i for i in doc.get("instances", [])}
    return flat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    old_flat = flatten(json.loads(args.old.read_text(encoding="utf-8")))
    new_flat = flatten(json.loads(args.new.read_text(encoding="utf-8")))

    added = {k: new_flat[k] for k in new_flat.keys() - old_flat.keys()}
    removed = {k: old_flat[k] for k in old_flat.keys() - new_flat.keys()}
    changed = {
        k: (old_flat[k], new_flat[k])
        for k in old_flat.keys() & new_flat.keys()
        if old_flat[k] != new_flat[k]
    }

    result = {
        "old": str(args.old),
        "new": str(args.new),
        "added": added,
        "removed": removed,
        "changed": {k: {"old": v[0], "new": v[1]} for k, v in changed.items()},
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not (added or removed or changed):
            print("no differences")
        for key, value in sorted(added.items()):
            print(f"+ {key} = {value}")
        for key, value in sorted(removed.items()):
            print(f"- {key} = {value}")
        for key, (old_value, new_value) in sorted(changed.items()):
            print(f"~ {key}: {old_value} -> {new_value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
