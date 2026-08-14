#!/usr/bin/env python3
"""Pure geometry math for test-coupon plates (fit trials before a long/expensive
print). No FreeCAD dependency — kept separate so it's testable standalone;
assets/freecad-parametric-template.FCMacro imports it to cut the actual solids.
"""

from __future__ import annotations


def feature_size(nominal: float, clearance: float) -> float:
    return nominal + clearance


def feature_positions(nominal, trial_values, spacing=15.0, margin=8.0):
    """Left-to-right (x_center, size) for each trial clearance, spaced so
    features never overlap."""
    positions = []
    x = margin
    for clearance in trial_values:
        size = feature_size(nominal, clearance)
        positions.append((x + size / 2, size))
        x += size + spacing
    return positions


def plate_dims(nominal, trial_values, spacing=15.0, margin=8.0):
    positions = feature_positions(nominal, trial_values, spacing, margin)
    last_x, last_size = positions[-1]
    width = last_x + last_size / 2 + margin
    depth = margin * 2 + max(feature_size(nominal, v) for v in trial_values)
    return width, depth


if __name__ == "__main__":
    trials = [0.15, 0.20, 0.25, 0.30]
    positions = feature_positions(5.0, trials)
    assert len(positions) == len(trials)
    for i in range(1, len(positions)):
        gap = positions[i][0] - positions[i - 1][0] - (positions[i - 1][1] + positions[i][1]) / 2
        assert gap > 0, f"features {i - 1} and {i} overlap"

    width, depth = plate_dims(5.0, trials)
    assert width > positions[-1][0] and depth > 0
    print("ok")
