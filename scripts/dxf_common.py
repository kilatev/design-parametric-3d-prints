#!/usr/bin/env python3
"""Shared ASCII DXF group-code pair parsing for the validate_* scripts."""

from __future__ import annotations

from pathlib import Path


def parse_pairs(path: Path) -> list[tuple[int, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"AutoCAD Binary DXF"):
        raise ValueError(f"{path}: binary DXF is not supported by this validator")
    lines = raw.decode("utf-8-sig").splitlines()
    if len(lines) % 2:
        raise ValueError(f"{path}: DXF has an odd number of group-code lines")
    pairs = []
    for index in range(0, len(lines), 2):
        try:
            code = int(lines[index].strip())
        except ValueError as exc:
            raise ValueError(f"{path}: invalid group code at line {index + 1}") from exc
        pairs.append((code, lines[index + 1].strip()))
    return pairs
