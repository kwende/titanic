# Geometry and camera model

This project uses ordinary perspective geometry. There is no need for a game engine or exotic projection.

## Units

One Blender unit is one meter.

The initial camera altitude is:

```text
2.5 statute miles × 1609.344 m/mile = 4023.36 m
```

This is the vertical distance from the local target/seabed reference to the camera during the graybox stage.

## Local coordinate convention

For the provisional scene:

- +X = local east/reference horizontal
- +Y = local north/reference vertical
- +Z = up
- Z = 0 is the nominal local seabed reference plane

The graybox origin is arbitrary.

During the site pass it should be replaced by a documented local frame derived from georeferenced source data.

## Perspective

For an object of size `s` viewed approximately normal to the camera at distance `h`:

```text
theta = 2 atan(s / (2h))
```

For small angles:

```text
theta ≈ s / h
```

The small-angle approximation is useful for intuition, but the exact expression is cheap and should be preferred for checks.

## Ground coverage

For a horizontal camera field of view `phi` and camera altitude `h`, the width of a flat target plane centered under the camera is:

```text
W = 2 h tan(phi / 2)
```

With the initial values:

```text
h   = 4023.36 m
phi = 60°
W   ≈ 4646 m
```

At 2560 horizontal pixels, a flat-plane center-of-frame rule of thumb is therefore on the order of:

```text
4646 / 2560 ≈ 1.8 m/pixel
```

This is not globally constant under perspective or over non-flat terrain, but it is enough to expose a useful fact: sub-meter wreck detail cannot drive the composition at this viewpoint.

## Apparent size must be earned

If a wreck component is difficult to see at the correct altitude, first try:

- better illumination;
- higher resolution;
- tonal/material separation;
- a modest FOV adjustment;
- a small camera orientation experiment.

Do not immediately change physical size or distance.

## Camera experiments

The graybox begins with a near-nadir view because it makes scale reasoning straightforward.

Possible later variants:

- exact nadir;
- small off-nadir tilt;
- slight lateral camera displacement;
- different horizontal FOVs while holding altitude fixed.

Every saved experiment should keep enough metadata to reproduce:

- camera position;
- camera target/orientation;
- horizontal FOV;
- render dimensions;
- scene scale.

## Terrain

The procedural terrain in the bootstrap script is intentionally fake low-frequency relief.

It exists only to:

- cast shadows;
- provide a non-flat visual field;
- teach the rendering workflow.

It must eventually be replaced with sourced bathymetry.

Do not tune the procedural terrain until it “looks like” the Titanic site and then mistake that resemblance for data.
