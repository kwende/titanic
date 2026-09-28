#!/usr/bin/env python3
"""
Generate the first Titanic "drained Atlantic" graybox scene.

Run from the repository root with:

    blender --background --python scripts/bootstrap_scene.py

The output is intentionally crude. Its job is to test scale, projection,
negative space, and the emotional effect of the geometry before detailed
modeling begins.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "graybox.json"
BUILD_DIR = REPO_ROOT / "build"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Remove orphaned collections created by repeated script runs in one session.
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)


def configure_scene(config: dict) -> bpy.types.Scene:
    scene = bpy.context.scene

    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0

    render = config["render"]
    scene.render.resolution_x = int(render["width_px"])
    scene.render.resolution_y = int(render["height_px"])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # Eevee is ideal for this first pass: the goal is fast iteration, not final
    # physically based rendering. Blender renamed the engine in newer releases.
    for engine_name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine_name
            break
        except TypeError:
            continue

    # Keep the world dark but not black so the graybox remains readable.
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.012, 0.016, 0.020, 1.0)
        background.inputs["Strength"].default_value = 0.18

    return scene


def make_material(name: str, rgba: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness

    material.diffuse_color = rgba
    return material


def terrain_height(x: float, y: float, terrain: dict) -> float:
    """
    Fake, intentionally low-frequency graybox relief.

    This is NOT Titanic bathymetry. It exists only to provide depth cues and
    shadows until sourced terrain replaces it.
    """
    amplitude = float(terrain["relief_amplitude_m"])
    slope = float(terrain["slope_x"]) * x + float(terrain["slope_y"]) * y

    undulation = amplitude * (
        0.50 * math.sin(x / 670.0)
        + 0.32 * math.cos(y / 910.0)
        + 0.18 * math.sin((x + y) / 1250.0)
    )
    return slope + undulation


def create_terrain(config: dict, material: bpy.types.Material) -> bpy.types.Object:
    terrain = config["terrain"]
    width = float(terrain["width_m"])
    depth = float(terrain["depth_m"])
    n = int(terrain["grid_resolution"])

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []

    for iy in range(n):
        fy = iy / (n - 1)
        y = -depth / 2.0 + fy * depth

        for ix in range(n):
            fx = ix / (n - 1)
            x = -width / 2.0 + fx * width
            z = terrain_height(x, y, terrain)
            vertices.append((x, y, z))

    for iy in range(n - 1):
        for ix in range(n - 1):
            a = iy * n + ix
            b = a + 1
            c = a + n + 1
            d = a + n
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("SeabedMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Seabed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["provisional"] = True
    obj["note"] = "Procedural graybox terrain; replace with sourced bathymetry."

    return obj


def create_box_proxy(
    name: str,
    spec: dict,
    terrain: dict,
    material: bpy.types.Material,
    bevel_m: float,
) -> bpy.types.Object:
    x, y, z_offset = (float(v) for v in spec["center_m"])
    length = float(spec["length_m"])
    beam = float(spec["beam_m"])
    height = float(spec["height_m"])
    heading = math.radians(float(spec["heading_deg"]))

    ground_z = terrain_height(x, y, terrain)

    bpy.ops.mesh.primitive_cube_add(
        location=(x, y, ground_z + z_offset + height / 2.0),
        rotation=(0.0, 0.0, heading),
    )
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (length, beam, height)

    # Apply only scale so bevel width is interpreted in meters.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bevel = obj.modifiers.new(name="Graybox bevel", type="BEVEL")
    bevel.width = bevel_m
    bevel.segments = 3

    obj.data.materials.append(material)
    obj["provisional"] = True
    obj["heading_deg"] = float(spec["heading_deg"])

    return obj


def append_box_geometry(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int, int]],
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    heading: float,
) -> None:
    """Append one rotated cuboid to a combined debris mesh."""
    cx, cy, cz = center
    sx, sy, sz = size
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0

    local = [
        (-hx, -hy, -hz),
        ( hx, -hy, -hz),
        ( hx,  hy, -hz),
        (-hx,  hy, -hz),
        (-hx, -hy,  hz),
        ( hx, -hy,  hz),
        ( hx,  hy,  hz),
        (-hx,  hy,  hz),
    ]

    cos_h = math.cos(heading)
    sin_h = math.sin(heading)
    base = len(vertices)

    for lx, ly, lz in local:
        rx = lx * cos_h - ly * sin_h
        ry = lx * sin_h + ly * cos_h
        vertices.append((cx + rx, cy + ry, cz + lz))

    faces.extend(
        [
            (base + 0, base + 1, base + 2, base + 3),
            (base + 4, base + 7, base + 6, base + 5),
            (base + 0, base + 4, base + 5, base + 1),
            (base + 1, base + 5, base + 6, base + 2),
            (base + 2, base + 6, base + 7, base + 3),
            (base + 4, base + 0, base + 3, base + 7),
        ]
    )


def create_debris(config: dict, material: bpy.types.Material) -> bpy.types.Object:
    debris = config["debris"]
    terrain = config["terrain"]

    cx, cy, _ = (float(v) for v in debris["center_m"])
    semi_major = float(debris["major_axis_m"]) / 2.0
    semi_minor = float(debris["minor_axis_m"]) / 2.0
    count = int(debris["count"])

    rng = random.Random(int(debris["seed"]))

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []

    for _ in range(count):
        # sqrt(random) gives a uniform point density over ellipse area.
        radius = math.sqrt(rng.random())
        angle = rng.uniform(0.0, math.tau)

        x = cx + semi_major * radius * math.cos(angle)
        y = cy + semi_minor * radius * math.sin(angle)

        # Most markers are only a few meters across. From ~4 km up they should
        # read as texture/speckle, not heroic chunks of wreckage.
        sx = rng.uniform(1.5, 7.0)
        sy = rng.uniform(1.0, 5.0)
        sz = rng.uniform(0.4, 2.2)
        heading = rng.uniform(0.0, math.tau)

        z = terrain_height(x, y, terrain) + sz / 2.0
        append_box_geometry(
            vertices,
            faces,
            center=(x, y, z),
            size=(sx, sy, sz),
            heading=heading,
        )

    mesh = bpy.data.meshes.new("DebrisProxyMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Debris proxies", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["provisional"] = True
    obj["note"] = "Deterministic graybox debris distribution; not archaeological data."

    return obj


def point_camera_at(camera: bpy.types.Object, target: Vector) -> None:
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_camera(config: dict) -> bpy.types.Object:
    camera_cfg = config["camera"]
    terrain = config["terrain"]

    target_x, target_y, target_z_offset = (
        float(v) for v in camera_cfg["target_m"]
    )
    ground_z = terrain_height(target_x, target_y, terrain)
    target = Vector((target_x, target_y, ground_z + target_z_offset))

    altitude = float(camera_cfg["altitude_m"])
    fov = math.radians(float(camera_cfg["horizontal_fov_deg"]))

    camera_data = bpy.data.cameras.new("TruthCamera")
    camera_data.type = "PERSP"
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.angle = fov
    camera_data.clip_start = 1.0
    camera_data.clip_end = 20000.0

    camera = bpy.data.objects.new("TruthCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera)

    camera.location = (target.x, target.y, target.z + altitude)
    point_camera_at(camera, target)

    camera["altitude_m"] = altitude
    camera["horizontal_fov_deg"] = float(camera_cfg["horizontal_fov_deg"])

    bpy.context.scene.camera = camera
    return camera


def create_sun() -> bpy.types.Object:
    light_data = bpy.data.lights.new(name="GrayboxSun", type="SUN")
    light_data.energy = 3.0
    light_data.angle = math.radians(2.0)

    sun = bpy.data.objects.new(name="GrayboxSun", object_data=light_data)
    bpy.context.scene.collection.objects.link(sun)

    # Deliberately low-ish directional light to make meter-scale relief legible.
    # This is an art-direction hypothesis, not a factual environmental claim.
    sun.rotation_euler = (
        math.radians(58.0),
        math.radians(-18.0),
        math.radians(32.0),
    )
    sun["provisional"] = True

    return sun


def report_projection(config: dict) -> None:
    camera_cfg = config["camera"]
    render = config["render"]

    altitude = float(camera_cfg["altitude_m"])
    horizontal_fov = math.radians(float(camera_cfg["horizontal_fov_deg"]))
    width_px = int(render["width_px"])

    ground_width = 2.0 * altitude * math.tan(horizontal_fov / 2.0)
    meters_per_pixel = ground_width / width_px

    print("")
    print("=== Titanic graybox projection ===")
    print(f"Camera altitude:       {altitude:,.2f} m")
    print(f"Horizontal FOV:        {math.degrees(horizontal_fov):.2f} deg")
    print(f"Flat ground coverage:  {ground_width:,.1f} m")
    print(f"Center rule-of-thumb:  {meters_per_pixel:.2f} m/px")
    print("==================================")
    print("")


def main() -> None:
    config = load_config()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    clear_scene()
    scene = configure_scene(config)

    seabed_material = make_material(
        "Seabed graybox",
        (0.095, 0.105, 0.105, 1.0),
        roughness=0.96,
    )
    wreck_material = make_material(
        "Wreck graybox",
        (0.18, 0.16, 0.135, 1.0),
        roughness=0.86,
    )
    debris_material = make_material(
        "Debris graybox",
        (0.13, 0.115, 0.095, 1.0),
        roughness=0.90,
    )

    create_terrain(config, seabed_material)

    wreck = config["wreck"]
    terrain = config["terrain"]

    create_box_proxy(
        "Bow proxy",
        wreck["bow"],
        terrain,
        wreck_material,
        bevel_m=4.0,
    )
    create_box_proxy(
        "Stern proxy",
        wreck["stern"],
        terrain,
        wreck_material,
        bevel_m=5.0,
    )

    create_debris(config, debris_material)
    create_camera(config)
    create_sun()

    report_projection(config)

    blend_path = BUILD_DIR / "titanic-graybox.blend"
    render_path = BUILD_DIR / "titanic-graybox.png"

    scene.render.filepath = str(render_path)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)

    print(f"Saved Blender scene: {blend_path}")
    print(f"Saved graybox render: {render_path}")


if __name__ == "__main__":
    main()
