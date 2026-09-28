#!/usr/bin/env python3
"""Render a large still at 90-degree horizontal FOV.

Run from the repository root with:

    blender --background --python scripts/render_90_large.py

This keeps the camera altitude, target, geometry, lighting, and physical scale
unchanged while rendering at 5120 x 2880. The terrain extent is derived with
the same margin used by the lens comparison so no mesh edge enters the frame.
"""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bootstrap_scene as graybox
import render_lens_comparison as lenses


def main() -> None:
    config = lenses.make_shared_config()
    config["camera"]["horizontal_fov_deg"] = 90.0
    config["render"]["width_px"] = 5120
    config["render"]["height_px"] = 2880

    scene = graybox.build_scene(config)
    scene["experiment"] = "Large 90 degree horizontal FOV graybox"
    scene["comparison_horizontal_fov_deg"] = 90.0
    graybox.save_and_render(scene, "titanic-90deg-5k")


if __name__ == "__main__":
    main()
