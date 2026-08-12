#!/usr/bin/env python3
"""Validate STL structure, bounds, bed contact, and optional empty regions."""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path


def load_binary(data: bytes):
    if len(data) < 84:
        raise ValueError("binary STL is shorter than 84 bytes")
    count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + 50 * count
    if len(data) != expected:
        raise ValueError(f"binary STL length mismatch: expected {expected}, got {len(data)}")
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        triangles.append((values[3:6], values[6:9], values[9:12]))
        offset += 50
    return triangles, "binary"


def load_ascii(data: bytes):
    text = data.decode("utf-8", errors="strict")
    vertices = []
    triangles = []
    for line in text.splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0].lower() == "vertex":
            vertices.append(tuple(float(v) for v in fields[1:]))
            if len(vertices) == 3:
                triangles.append(tuple(vertices))
                vertices = []
    if not triangles or vertices:
        raise ValueError("invalid or empty ASCII STL")
    return triangles, "ascii"


def load_stl(path: Path):
    data = path.read_bytes()
    if data.lstrip(b" \t\r\n")[:5].lower() == b"solid":
        return load_ascii(data)
    try:
        return load_binary(data)
    except (ValueError, struct.error):
        return load_ascii(data)


def parse_triplet(value: str):
    parts = [float(x) for x in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected X,Y,Z")
    return parts


def parse_region(value: str):
    parts = [float(x) for x in value.split(",")]
    if len(parts) != 6:
        raise argparse.ArgumentTypeError("expected XMIN,XMAX,YMIN,YMAX,ZMIN,ZMAX")
    if not (parts[0] <= parts[1] and parts[2] <= parts[3] and parts[4] <= parts[5]):
        raise argparse.ArgumentTypeError("region minima must not exceed maxima")
    return parts


def edge_cross(tri):
    a, b, c = tri
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def triangle_area(tri):
    cross = edge_cross(tri)
    return 0.5 * math.sqrt(sum(x * x for x in cross))


def dedup_vertex_ids(triangles, tolerance):
    decimals = max(0, min(6, round(-math.log10(tolerance)))) if tolerance > 0 else 6
    index: dict[tuple, int] = {}
    ids = []
    for tri in triangles:
        tri_ids = []
        for v in tri:
            key = tuple(round(c, decimals) for c in v)
            tri_ids.append(index.setdefault(key, len(index)))
        ids.append(tri_ids)
    return ids


def mesh_topology(triangles, tolerance):
    """Return (non_manifold_edge_count, flipped_normal_edge_count, component_count)."""
    ids = dedup_vertex_ids(triangles, tolerance)

    undirected_count: Counter = Counter()
    directed_by_edge: dict[frozenset, list[tuple[int, int]]] = defaultdict(list)
    edge_to_triangles: dict[frozenset, list[int]] = defaultdict(list)
    for tri_index, tri_ids in enumerate(ids):
        for a, b in ((tri_ids[0], tri_ids[1]), (tri_ids[1], tri_ids[2]), (tri_ids[2], tri_ids[0])):
            key = frozenset((a, b))
            undirected_count[key] += 1
            directed_by_edge[key].append((a, b))
            edge_to_triangles[key].append(tri_index)

    non_manifold = sum(1 for count in undirected_count.values() if count != 2)
    flipped = sum(1 for dirs in directed_by_edge.values() if len(dirs) == 2 and dirs[0] == dirs[1])

    parent = list(range(len(triangles)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for tris in edge_to_triangles.values():
        for other in tris[1:]:
            union(tris[0], other)
    components = len({find(i) for i in range(len(triangles))}) if triangles else 0

    return non_manifold, flipped, components


def overhang_angle_deg(tri):
    """Angle from vertical (0 = vertical wall, 90 = flat downward-facing ceiling)
    for a downward-facing triangle, or None if the triangle faces up/sideways.
    Convention: only downward-facing normals (nz < 0) are overhangs at all;
    a vertical wall is never flagged regardless of the chosen threshold.
    """
    cross = edge_cross(tri)
    length = math.sqrt(sum(x * x for x in cross))
    if length <= 0:
        return None
    nz = cross[2] / length
    if nz >= 0:
        return None
    return math.degrees(math.asin(min(1.0, abs(nz))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stl", type=Path)
    parser.add_argument("--bed-z", type=float, default=0.0)
    parser.add_argument("--tolerance", type=float, default=1e-4)
    parser.add_argument("--expect-size", type=parse_triplet)
    parser.add_argument("--size-tolerance", type=float, default=0.05)
    parser.add_argument("--min-contact-x", type=float, default=0.0)
    parser.add_argument("--min-contact-y", type=float, default=0.0)
    parser.add_argument("--empty-region", type=parse_region, action="append", default=[])
    parser.add_argument("--expect-components", type=int)
    parser.add_argument("--allow-non-manifold", action="store_true")
    parser.add_argument("--max-overhang", type=float, help="degrees from vertical; flag downward-facing triangles steeper than this")
    parser.add_argument("--bed-size", type=parse_triplet, help="X,Y,Z build volume; flags a model that doesn't fit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    triangles, encoding = load_stl(args.stl)
    vertices = [vertex for tri in triangles for vertex in tri]
    if not all(math.isfinite(v) for point in vertices for v in point):
        raise SystemExit("FAIL: non-finite STL coordinate")

    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]
    size = [maxs[i] - mins[i] for i in range(3)]
    contact = [v for v in vertices if abs(v[2] - args.bed_z) <= args.tolerance]
    below = sum(v[2] < args.bed_z - args.tolerance for v in vertices)
    degenerate = sum(triangle_area(t) <= args.tolerance * args.tolerance for t in triangles)
    contact_span = [0.0, 0.0]
    if contact:
        contact_span = [
            max(v[0] for v in contact) - min(v[0] for v in contact),
            max(v[1] for v in contact) - min(v[1] for v in contact),
        ]

    non_manifold_edges, flipped_normal_edges, components = mesh_topology(triangles, args.tolerance)

    overhang_triangles = 0
    max_overhang_seen = 0.0
    if args.max_overhang is not None:
        for tri in triangles:
            centroid_z = sum(v[2] for v in tri) / 3
            if centroid_z <= args.bed_z + args.tolerance:
                continue  # resting on the bed, not a floating overhang
            angle = overhang_angle_deg(tri)
            if angle is not None:
                max_overhang_seen = max(max_overhang_seen, angle)
                if angle > args.max_overhang:
                    overhang_triangles += 1

    region_hits = []
    for region in args.empty_region:
        xmin, xmax, ymin, ymax, zmin, zmax = region
        hits = 0
        for tri in triangles:
            center = [sum(v[i] for v in tri) / 3 for i in range(3)]
            if xmin < center[0] < xmax and ymin < center[1] < ymax and zmin < center[2] < zmax:
                hits += 1
        region_hits.append(hits)

    failures = []
    if below:
        failures.append(f"{below} vertices below bed Z={args.bed_z}")
    if not contact:
        failures.append(f"no vertices contact bed Z={args.bed_z}")
    if degenerate:
        failures.append(f"{degenerate} degenerate triangles")
    if args.expect_size:
        for axis, actual, expected in zip("XYZ", size, args.expect_size):
            if abs(actual - expected) > args.size_tolerance:
                failures.append(f"size {axis}={actual:.4f}, expected {expected:.4f}")
    if contact_span[0] + args.tolerance < args.min_contact_x:
        failures.append(f"contact X span {contact_span[0]:.4f} < {args.min_contact_x:.4f}")
    if contact_span[1] + args.tolerance < args.min_contact_y:
        failures.append(f"contact Y span {contact_span[1]:.4f} < {args.min_contact_y:.4f}")
    for region, hits in zip(args.empty_region, region_hits):
        if hits:
            failures.append(f"empty region {region} contains {hits} triangle centroids")
    if not args.allow_non_manifold and non_manifold_edges:
        failures.append(f"{non_manifold_edges} non-manifold edges (not shared by exactly two triangles)")
    if not args.allow_non_manifold and flipped_normal_edges:
        failures.append(f"{flipped_normal_edges} edges with inconsistent winding (flipped normals)")
    if args.expect_components is not None and components != args.expect_components:
        failures.append(f"{components} connected components, expected {args.expect_components}")
    if args.max_overhang is not None and overhang_triangles:
        failures.append(
            f"{overhang_triangles} downward-facing triangles exceed {args.max_overhang}° from vertical "
            f"(steepest {max_overhang_seen:.1f}°) — face-angle only, doesn't know if a wedge/support already sits under it"
        )
    if args.bed_size is not None:
        for axis, actual, limit in zip("XYZ", size, args.bed_size):
            if actual > limit + args.tolerance:
                failures.append(f"size {axis}={actual:.4f} exceeds build volume {limit:.4f}")

    result = {
        "file": str(args.stl),
        "encoding": encoding,
        "triangles": len(triangles),
        "bounds_min": mins,
        "bounds_max": maxs,
        "size": size,
        "bed_z": args.bed_z,
        "contact_vertices": len(contact),
        "contact_span_xy": contact_span,
        "vertices_below_bed": below,
        "degenerate_triangles": degenerate,
        "empty_region_hits": region_hits,
        "non_manifold_edges": non_manifold_edges,
        "flipped_normal_edges": flipped_normal_edges,
        "connected_components": components,
        "overhang_triangles": overhang_triangles if args.max_overhang is not None else None,
        "max_overhang_seen_deg": max_overhang_seen if args.max_overhang is not None else None,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.stl}: {encoding}, {len(triangles)} triangles")
        print(f"bounds: {mins} .. {maxs}; size: {size}")
        print(f"bed contact: {len(contact)} vertices; span X/Y: {contact_span}")
        for failure in failures:
            print(f"FAIL: {failure}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
