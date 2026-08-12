#!/usr/bin/env python3
"""Smoke tests for scripts/*.py. Plain asserts, no framework: `python3 scripts/test_validators.py`."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import dxf_common
import estimate_material
import validate_dxf
import validate_projections
import validate_stl
import diff_parameters

HERE = Path(__file__).parent

DXF_TEXT = "\n".join(
    [
        "0", "SECTION", "2", "ENTITIES",
        "0", "LINE", "8", "0", "10", "0", "20", "0", "30", "0", "11", "1", "21", "1", "31", "0",
        "0", "TEXT", "8", "0", "1", "R2",
        "0", "ENDSEC",
        "0", "EOF",
    ]
) + "\n"

TETRAHEDRON = [
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
]

UNIT_CUBE = [
    ((0, 0, 0), (1, 0, 0), (1, 1, 0)), ((0, 0, 0), (1, 1, 0), (0, 1, 0)),
    ((0, 0, 1), (1, 1, 1), (1, 0, 1)), ((0, 0, 1), (0, 1, 1), (1, 1, 1)),
    ((0, 0, 0), (0, 1, 0), (0, 1, 1)), ((0, 0, 0), (0, 1, 1), (0, 0, 1)),
    ((1, 0, 0), (1, 1, 1), (1, 1, 0)), ((1, 0, 0), (1, 0, 1), (1, 1, 1)),
    ((0, 0, 0), (1, 0, 1), (1, 0, 0)), ((0, 0, 0), (0, 0, 1), (1, 0, 1)),
    ((0, 1, 0), (1, 1, 0), (1, 1, 1)), ((0, 1, 0), (1, 1, 1), (0, 1, 1)),
]


def check_dxf_common(tmp: Path):
    good = tmp / "good.dxf"
    good.write_text(DXF_TEXT, encoding="utf-8")
    pairs = dxf_common.parse_pairs(good)
    assert (2, "ENTITIES") in pairs
    assert pairs[-1] == (0, "EOF")

    odd = tmp / "odd.dxf"
    odd.write_text("0\nSECTION\n2\n", encoding="utf-8")
    try:
        dxf_common.parse_pairs(odd)
        assert False, "expected odd-line-count DXF to raise"
    except ValueError:
        pass

    binary = tmp / "binary.dxf"
    binary.write_bytes(b"AutoCAD Binary DXF\r\n\x1a\x00")
    try:
        dxf_common.parse_pairs(binary)
        assert False, "expected binary DXF signature to raise"
    except ValueError:
        pass
    print("ok: dxf_common.parse_pairs")


def check_validate_dxf_helpers():
    pairs = [
        (0, "SECTION"), (2, "TABLES"),
        (0, "LAYER"), (2, "MYLAYER"),
        (0, "ENDSEC"),
        (0, "SECTION"), (2, "ENTITIES"),
        (0, "LINE"), (8, "MYLAYER"), (10, "0"), (20, "0"),
        (0, "TEXT"), (8, "MYLAYER"), (1, "R3"),
        (0, "ENDSEC"),
        (0, "EOF"),
    ]
    records = validate_dxf.entity_records(pairs)
    kinds = [kind for kind, _ in records]
    assert kinds == ["LINE", "TEXT"], kinds
    assert validate_dxf.first(records[0][1], 8) == "MYLAYER"

    table_pairs = validate_dxf.tables_section(pairs)
    declared = {
        v for i, (c, v) in enumerate(table_pairs)
        if c == 2 and i > 0 and table_pairs[i - 1] == (0, "LAYER")
    }
    assert declared == {"MYLAYER"}
    print("ok: validate_dxf.entity_records/first/tables_section")


def check_validate_projections_helpers():
    pairs = [(10, "0"), (20, "0"), (11, "5"), (21, "3"), (1, "R2")]
    b = validate_projections.bounds(pairs)
    assert b["x"] == (0.0, 5.0)
    assert b["y"] == (0.0, 3.0)
    assert validate_projections.envelope(b, "x") == 5.0
    assert validate_projections.revision_marks(pairs) == {"R2"}
    print("ok: validate_projections.bounds/envelope/revision_marks")


def check_validate_stl_helpers():
    right_triangle = ((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 4.0, 0.0))
    assert abs(validate_stl.triangle_area(right_triangle) - 6.0) < 1e-9

    non_manifold, flipped, components = validate_stl.mesh_topology(TETRAHEDRON, 1e-6)
    assert non_manifold == 0, non_manifold
    assert components == 1, components

    open_shell = [TETRAHEDRON[0]]
    non_manifold_open, _, components_open = validate_stl.mesh_topology(open_shell, 1e-6)
    assert non_manifold_open == 3, non_manifold_open
    assert components_open == 1, components_open
    print("ok: validate_stl.triangle_area/mesh_topology (edge_cross)")


def check_estimate_material():
    volume = estimate_material.signed_volume(UNIT_CUBE)
    assert abs(volume - 1.0) < 1e-9, volume
    print("ok: estimate_material.signed_volume")


def check_diff_parameters_flatten():
    doc = {
        "revision": "R1",
        "units": "mm",
        "nominal": {"x": 10},
        "instances": [{"name": "wheel_fl", "position": [0, 0, 0]}],
    }
    flat = diff_parameters.flatten(doc)
    assert flat["revision"] == "R1"
    assert flat["nominal.x"] == 10
    assert flat["instances.wheel_fl"] == {"name": "wheel_fl", "position": [0, 0, 0]}
    print("ok: diff_parameters.flatten")


def run_cli(args) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, *args], capture_output=True, text=True
    )
    return result.returncode, json.loads(result.stdout)


def check_validate_manifest_cli(tmp: Path):
    (tmp / "part.step").write_text("x", encoding="utf-8")
    (tmp / "part.stl").write_text("x", encoding="utf-8")
    (tmp / "part.FCMacro").write_text("x", encoding="utf-8")
    good = tmp / "manifest.json"
    good.write_text(json.dumps({
        "revision": "R1", "units": "mm", "approved_drawing": "part.FCMacro",
        "files": {"source": "part.FCMacro", "step": "part.step", "stl": "part.stl"},
    }), encoding="utf-8")
    code, out = run_cli([str(HERE / "validate_manifest.py"), str(good), "--json"])
    assert code == 0, out
    assert out["failures"] == []

    bad = tmp / "bad_manifest.json"
    bad.write_text(json.dumps({
        "revision": "R1", "units": "mm", "approved_drawing": "part.FCMacro",
        "files": {"source": "part.FCMacro", "step": "missing.step", "stl": "part.stl"},
    }), encoding="utf-8")
    code, out = run_cli([str(HERE / "validate_manifest.py"), str(bad), "--json"])
    assert code == 1
    assert any("missing.step" in f for f in out["failures"]), out

    escape = tmp / "escape_manifest.json"
    escape.write_text(json.dumps({
        "revision": "R1", "units": "mm", "approved_drawing": "part.FCMacro",
        "files": {"source": "part.FCMacro", "step": "../../etc/passwd", "stl": "part.stl"},
    }), encoding="utf-8")
    code, out = run_cli([str(HERE / "validate_manifest.py"), str(escape), "--json"])
    assert code == 1
    assert any("escapes manifest directory" in f for f in out["failures"]), out
    print("ok: validate_manifest.py CLI (pass/fail/path-escape)")


def check_validate_step_cli(tmp: Path):
    good = tmp / "good.step"
    good.write_text(
        "ISO-10303-21;\n#1=PRODUCT('bracket');\n#2=MANIFOLD_SOLID_BREP(#1);\nEND-ISO-10303-21;\n",
        encoding="utf-8",
    )
    code, out = run_cli([str(HERE / "validate_step.py"), str(good), "--expect-product", "bracket", "--json"])
    assert code == 0, out
    assert out["failures"] == []

    bad = tmp / "bad.step"
    bad.write_text("not a step file", encoding="utf-8")
    code, out = run_cli([str(HERE / "validate_step.py"), str(bad), "--json"])
    assert code == 1
    assert out["failures"]
    print("ok: validate_step.py CLI (pass/fail)")


def check_diff_parameters_cli(tmp: Path):
    old = tmp / "old.json"
    new = tmp / "new.json"
    old.write_text(json.dumps({"revision": "R1", "nominal": {"x": 10}}), encoding="utf-8")
    new.write_text(json.dumps({"revision": "R2", "nominal": {"x": 12}}), encoding="utf-8")
    code, out = run_cli([str(HERE / "diff_parameters.py"), str(old), str(new), "--json"])
    assert code == 0
    assert out["changed"]["nominal.x"] == {"old": 10, "new": 12}
    assert out["changed"]["revision"] == {"old": "R1", "new": "R2"}
    print("ok: diff_parameters.py CLI")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        check_dxf_common(tmp)
        check_validate_dxf_helpers()
        check_validate_projections_helpers()
        check_validate_stl_helpers()
        check_estimate_material()
        check_diff_parameters_flatten()
        check_validate_manifest_cli(tmp)
        check_validate_step_cli(tmp)
        check_diff_parameters_cli(tmp)
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
