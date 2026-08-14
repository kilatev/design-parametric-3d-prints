#!/usr/bin/env python3
"""Pure geometry math for a print-in-place pin-in-sleeve joint (a hinge/swivel
that prints already assembled, with a functional gap between its two halves).
No FreeCAD dependency — testable standalone;
assets/freecad-parametric-template.FCMacro imports it to cut the actual solids.
"""

from __future__ import annotations

import math


def sleeve_dims(pin_radius, radial_clearance, wall_thickness, pin_height, axial_play):
    """Sleeve inner/outer radius and height for a pin of the given radius and
    height. axial_play is the end-float gap on *each* end of the pin, kept
    separate from radial_clearance because elephant's foot and bridging hit
    the two very differently."""
    inner_r = pin_radius + radial_clearance
    outer_r = inner_r + wall_thickness
    sleeve_h = pin_height + 2 * axial_play
    return inner_r, outer_r, sleeve_h


def pin_z_offset(standoff_from_bed, axial_play):
    """Z of the pin's bottom face: lifted off the bed (standoff) and further
    centred inside the sleeve by one axial_play gap."""
    return standoff_from_bed + axial_play


def rib_positions(rib_count):
    """Evenly spaced angles (degrees) for bore-relief contact ribs around a
    sleeve's inner wall."""
    return [i * 360.0 / rib_count for i in range(rib_count)]


def rib_box_dims(inner_r, relief_depth, rib_width_deg):
    """Flat-box approximation of one relief rib: a small radial land that
    stays at inner_r while the rest of the bore is relieved outward by
    relief_depth. The rib is modelled as a flat box, not a true conforming
    arc — a good approximation for the narrow rib widths (<=30 deg) this is
    meant for. Returns (radial_depth, tangential_chord)."""
    chord = 2 * inner_r * math.sin(math.radians(rib_width_deg) / 2)
    return relief_depth, chord


def joint_grid_positions(pin_radius, wall_thickness, radial_values, axial_values, margin=8.0, spacing=None):
    """Grid layout for a 2D print-in-place test coupon: rows vary
    radial_clearance (radial_values), columns vary axial_play (axial_values).
    spacing auto-sizes from the largest resulting sleeve OD when not given,
    the same non-overlap reasoning as coupon_plate.feature_positions."""
    if spacing is None:
        max_outer_d = 2 * (pin_radius + max(radial_values) + wall_thickness)
        spacing = max_outer_d + margin
    return [
        (margin + i * spacing, margin + j * spacing, radial, axial)
        for i, radial in enumerate(radial_values)
        for j, axial in enumerate(axial_values)
    ]


if __name__ == "__main__":
    inner_r, outer_r, sleeve_h = sleeve_dims(
        pin_radius=2.0, radial_clearance=0.25, wall_thickness=1.2, pin_height=10.0, axial_play=0.3
    )
    assert inner_r > 2.0
    assert outer_r > inner_r
    assert sleeve_h > 10.0

    z = pin_z_offset(standoff_from_bed=1.0, axial_play=0.3)
    assert z == 1.3

    angles = rib_positions(3)
    assert angles == [0.0, 120.0, 240.0]

    depth, chord = rib_box_dims(inner_r=2.25, relief_depth=0.3, rib_width_deg=20)
    assert depth == 0.3
    assert 0 < chord < 2 * 2.25

    positions = joint_grid_positions(
        pin_radius=2.0, wall_thickness=1.2, radial_values=[0.15, 0.25], axial_values=[0.2, 0.3, 0.4]
    )
    assert len(positions) == 2 * 3
    xs = sorted({x for x, y, r, a in positions})
    ys = sorted({y for x, y, r, a in positions})
    assert len(xs) == 2 and len(ys) == 3
    min_spacing = min(b - a for a, b in zip(xs, xs[1:]))
    max_outer_d = 2 * (2.0 + 0.25 + 1.2)
    assert min_spacing >= max_outer_d

    print("ok")
