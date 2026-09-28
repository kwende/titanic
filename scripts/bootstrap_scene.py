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

    # Comparison scripts rebuild several scenes in one Blender process. Remove
    # unlinked data so later .blend files contain only their own experiment.
    for data_blocks in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for data_block in list(data_blocks):
            if data_block.users == 0:
                data_blocks.remove(data_block)


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
    scene.render.image_settings.color_mode = "RGBA"

    # Eevee is ideal for this first pass: the goal is fast iteration, not final
    # physically based rendering. Blender renamed the engine in newer releases.
    for engine_name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine_name
            break
        except TypeError:
            continue

    # The sample budget is an explicit graybox tradeoff: enough edge/shadow
    # stability to evaluate the composition without turning this into a final
    # render pipeline.
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = int(render["samples"])

    scene.view_settings.look = "AgX - Medium High Contrast"

    # Keep the world dark but not black so unlit faces retain enough context.
    look = config["look"]
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = tuple(look["world_color_linear"])
        background.inputs["Strength"].default_value = float(look["world_strength"])

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


def make_seabed_material(config: dict) -> bpy.types.Material:
    """Build restrained, deterministic tonal variation at terrain scale."""
    look = config["look"]
    material = bpy.data.materials.new(name="Seabed graybox")
    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        return material

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "Terrain coordinates"
    texcoord.location = (-620.0, 0.0)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "Provisional broad seabed variation"
    noise.location = (-400.0, 0.0)
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = float(look["seabed_noise_scale"])
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.58

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "Restrained seabed values"
    ramp.location = (-170.0, 0.0)
    ramp.color_ramp.interpolation = "B_SPLINE"
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = tuple(look["seabed_dark_linear"])
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = tuple(look["seabed_light_linear"])

    bsdf.inputs["Roughness"].default_value = 0.97
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
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
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    obj = bpy.data.objects.new("Seabed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["provisional"] = True
    obj["note"] = "Procedural graybox terrain; replace with sourced bathymetry."

    return obj


def create_prism_proxy(
    name: str,
    spec: dict,
    terrain: dict,
    material: bpy.types.Material,
    bevel_m: float,
    footprint: list[tuple[float, float]],
) -> bpy.types.Object:
    """Create a low-poly wreck prism inside the configured metric bounds."""
    x, y, z_offset = (float(v) for v in spec["center_m"])
    length = float(spec["length_m"])
    beam = float(spec["beam_m"])
    height = float(spec["height_m"])
    heading = math.radians(float(spec["heading_deg"]))

    ground_z = terrain_height(x, y, terrain)

    count = len(footprint)
    vertices = [
        (nx * length, ny * beam, z)
        for z in (0.0, height)
        for nx, ny in footprint
    ]
    faces: list[tuple[int, ...]] = [
        tuple(reversed(range(count))),
        tuple(count + i for i in range(count)),
    ]
    for i in range(count):
        next_i = (i + 1) % count
        faces.append((i, next_i, count + next_i, count + i))

    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (x, y, ground_z + z_offset)
    obj.rotation_euler = (0.0, 0.0, heading)

    bevel = obj.modifiers.new(name="Graybox bevel", type="BEVEL")
    bevel.width = bevel_m
    bevel.segments = 3

    obj.data.materials.append(material)
    obj["provisional"] = True
    obj["heading_deg"] = float(spec["heading_deg"])
    obj["note"] = "Low-poly silhouette proxy; dimensions and shape remain provisional."

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


def projection_metrics(config: dict) -> dict[str, float]:
    camera_cfg = config["camera"]
    render = config["render"]

    altitude = float(camera_cfg["altitude_m"])
    horizontal_fov = math.radians(float(camera_cfg["horizontal_fov_deg"]))
    width_px = int(render["width_px"])
    height_px = int(render["height_px"])

    ground_width = 2.0 * altitude * math.tan(horizontal_fov / 2.0)
    ground_height = ground_width * height_px / width_px
    return {
        "ground_width_m": ground_width,
        "ground_height_m": ground_height,
        "meters_per_pixel": ground_width / width_px,
    }


def validate_config(config: dict) -> None:
    """Reject framing mistakes that would invalidate the visual scale test."""
    camera = config["camera"]
    terrain = config["terrain"]
    debris = config["debris"]
    metrics = projection_metrics(config)

    altitude = float(camera["altitude_m"])
    fov_deg = float(camera["horizontal_fov_deg"])
    if altitude <= 0.0:
        raise ValueError("camera.altitude_m must be positive")
    if not 0.0 < fov_deg < 180.0:
        raise ValueError("camera.horizontal_fov_deg must be between 0 and 180")
    if int(terrain["grid_resolution"]) < 2:
        raise ValueError("terrain.grid_resolution must be at least 2")

    if float(terrain["width_m"]) < metrics["ground_width_m"]:
        raise ValueError("terrain.width_m does not cover the camera's flat-plane view")
    if float(terrain["depth_m"]) < metrics["ground_height_m"]:
        raise ValueError("terrain.depth_m does not cover the camera's flat-plane view")

    debris_x, debris_y, _ = (float(v) for v in debris["center_m"])
    debris_half_width = float(debris["major_axis_m"]) / 2.0
    debris_half_depth = float(debris["minor_axis_m"]) / 2.0
    if abs(debris_x) + debris_half_width > float(terrain["width_m"]) / 2.0:
        raise ValueError("debris major-axis bounds extend beyond the terrain")
    if abs(debris_y) + debris_half_depth > float(terrain["depth_m"]) / 2.0:
        raise ValueError("debris minor-axis bounds extend beyond the terrain")


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


def create_sun(config: dict) -> bpy.types.Object:
    lighting = config["lighting"]
    light_data = bpy.data.lights.new(name="GrayboxSun", type="SUN")
    light_data.energy = float(lighting["energy"])
    light_data.angle = math.radians(float(lighting["angular_diameter_deg"]))

    sun = bpy.data.objects.new(name="GrayboxSun", object_data=light_data)
    bpy.context.scene.collection.objects.link(sun)

    # Deliberately low-ish directional light to make meter-scale relief legible.
    # This is an art-direction hypothesis, not a factual environmental claim.
    sun.rotation_euler = tuple(
        math.radians(float(degrees)) for degrees in lighting["rotation_deg"]
    )
    sun["provisional"] = True

    return sun


def report_projection(config: dict) -> None:
    camera_cfg = config["camera"]
    wreck = config["wreck"]
    debris = config["debris"]

    altitude = float(camera_cfg["altitude_m"])
    horizontal_fov = math.radians(float(camera_cfg["horizontal_fov_deg"]))
    metrics = projection_metrics(config)
    meters_per_pixel = metrics["meters_per_pixel"]

    bow_x, bow_y, _ = (float(v) for v in wreck["bow"]["center_m"])
    stern_x, stern_y, _ = (float(v) for v in wreck["stern"]["center_m"])
    wreck_separation = math.hypot(stern_x - bow_x, stern_y - bow_y)

    print("")
    print("=== Titanic graybox projection ===")
    print(f"Camera altitude:       {altitude:,.2f} m")
    print(f"Horizontal FOV:        {math.degrees(horizontal_fov):.2f} deg")
    print(
        "Flat ground coverage:  "
        f"{metrics['ground_width_m']:,.1f} x {metrics['ground_height_m']:,.1f} m"
    )
    print(f"Center rule-of-thumb:  {meters_per_pixel:.2f} m/px")
    print(
        "Bow proxy length:      "
        f"{float(wreck['bow']['length_m']) / meters_per_pixel:.1f} px"
    )
    print(f"Wreck-center spacing:  {wreck_separation / meters_per_pixel:.1f} px")
    print(
        "Debris footprint:      "
        f"{float(debris['major_axis_m']) / meters_per_pixel:.1f} x "
        f"{float(debris['minor_axis_m']) / meters_per_pixel:.1f} px"
    )
    print("Configuration checks:  PASS")
    print("==================================")
    print("")


def build_scene(config: dict) -> bpy.types.Scene:
    """Construct one complete graybox scene from an already-derived config."""
    validate_config(config)
    clear_scene()
    scene = configure_scene(config)

    look = config["look"]
    seabed_material = make_seabed_material(config)
    wreck_material = make_material(
        "Wreck graybox",
        tuple(look["wreck_color_linear"]),
        roughness=0.86,
    )
    debris_material = make_material(
        "Debris graybox",
        tuple(look["debris_color_linear"]),
        roughness=0.90,
    )

    create_terrain(config, seabed_material)

    wreck = config["wreck"]
    terrain = config["terrain"]

    create_prism_proxy(
        "Bow proxy",
        wreck["bow"],
        terrain,
        wreck_material,
        bevel_m=2.0,
        # Flat break at -X; a simple pointed bow at +X.
        footprint=[(-0.5, -0.5), (0.18, -0.5), (0.5, 0.0), (0.18, 0.5), (-0.5, 0.5)],
    )
    create_prism_proxy(
        "Stern proxy",
        wreck["stern"],
        terrain,
        wreck_material,
        bevel_m=3.0,
        # Asymmetry distinguishes the damaged stern without pretending to model it.
        footprint=[(-0.5, -0.5), (0.5, -0.5), (0.42, 0.36), (0.10, 0.5), (-0.5, 0.30)],
    )

    create_debris(config, debris_material)
    create_camera(config)
    create_sun(config)

    report_projection(config)
    return scene


def save_and_render(scene: bpy.types.Scene, output_stem: str) -> tuple[Path, Path]:
    """Save a reproducible scene and render using a shared output stem."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    blend_path = BUILD_DIR / f"{output_stem}.blend"
    render_path = BUILD_DIR / f"{output_stem}.png"

    scene.render.filepath = str(render_path)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)

    print(f"Saved Blender scene: {blend_path}")
    print(f"Saved graybox render: {render_path}")
    return blend_path, render_path


def main() -> None:
    config = load_config()
    scene = build_scene(config)
    save_and_render(scene, "titanic-graybox")


if __name__ == "__main__":
    main()
