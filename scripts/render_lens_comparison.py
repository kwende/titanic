#!/usr/bin/env python3
"""Render the same graybox through 60, 75, and 90 degree horizontal FOVs.

Run from the repository root with:

    blender --background --python scripts/render_lens_comparison.py

The camera altitude, target, geometry, lighting, and output resolution stay
fixed. Only horizontal FOV changes. A shared expanded terrain prevents the
wider frames from exposing the edge of the provisional seabed mesh.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bootstrap_scene as graybox


HORIZONTAL_FOV_DEGREES = (60.0, 75.0, 90.0)
TERRAIN_MARGIN = 1.08
TERRAIN_ROUNDING_M = 100.0


def round_up(value: float, increment: float) -> float:
    return math.ceil(value / increment) * increment


def make_shared_config() -> dict:
    """Derive one terrain extent large enough for every comparison frame."""
    config = graybox.load_config()
    widest = copy.deepcopy(config)
    widest["camera"]["horizontal_fov_deg"] = max(HORIZONTAL_FOV_DEGREES)
    coverage = graybox.projection_metrics(widest)

    terrain = config["terrain"]
    original_spacing = float(terrain["width_m"]) / (
        int(terrain["grid_resolution"]) - 1
    )
    required_extent = max(
        float(terrain["width_m"]),
        float(terrain["depth_m"]),
        coverage["ground_width_m"] * TERRAIN_MARGIN,
        coverage["ground_height_m"] * TERRAIN_MARGIN,
    )
    shared_extent = round_up(required_extent, TERRAIN_ROUNDING_M)

    terrain["width_m"] = shared_extent
    terrain["depth_m"] = shared_extent
    terrain["grid_resolution"] = round(shared_extent / original_spacing) + 1
    return config


def main() -> None:
    shared_config = make_shared_config()
    terrain = shared_config["terrain"]
    print(
        "Lens comparison terrain: "
        f"{terrain['width_m']:.0f} x {terrain['depth_m']:.0f} m, "
        f"{terrain['grid_resolution']} x {terrain['grid_resolution']} vertices"
    )

    for fov_deg in HORIZONTAL_FOV_DEGREES:
        config = copy.deepcopy(shared_config)
        config["camera"]["horizontal_fov_deg"] = fov_deg
        scene = graybox.build_scene(config)
        scene["experiment"] = "Horizontal FOV comparison"
        scene["comparison_horizontal_fov_deg"] = fov_deg
        graybox.save_and_render(scene, f"titanic-lens-{int(fov_deg)}deg")


if __name__ == "__main__":
    main()
