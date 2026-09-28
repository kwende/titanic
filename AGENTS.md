# AGENTS.md

## Mission

Create a single visually striking but metrically disciplined image of the RMS Titanic wreck site as if the North Atlantic had been drained and the viewer were approximately 2.5 miles / 4,023 m above the seabed.

The image should make the wreck feel disturbingly small, isolated, and far below the world above it.

This is not a game, simulator, interactive experience, or general-purpose Titanic digital twin.

## Prime directive

**Build the truth first; then make the truth beautiful.**

The emotional effect must come from honest scale.

Never silently make the wreck larger, move the bow and stern closer together, shrink the debris field, lower the camera, increase vertical relief, or otherwise falsify scale merely to improve readability.

Legibility may be improved with lighting, materials, resolution, local contrast, and composition.

## Current stage

The project begins in the **graybox / truth pass**.

The current scene values are intentionally provisional except where documented otherwise. Do not present placeholder dimensions, orientations, terrain, or debris distributions as established archaeological facts.

Before replacing a provisional value with a supposedly factual one:

1. identify the source;
2. record the source/provenance;
3. state what was measured versus inferred;
4. preserve uncertainty when the evidence is approximate.

Do not invent precision.

## Collaboration style

The owner is a software engineer learning Blender and visual design while building this project.

Do not turn the repository into opaque agent-generated machinery.

When making a meaningful visual, geometric, or Blender decision:

- explain the governing idea briefly;
- prefer first-principles reasoning over Blender folklore;
- make the result reproducible in code/config when practical;
- keep important constants visible and named;
- leave enough structure that a human can reconstruct why the scene works.

Avoid giant frameworks. This is one image.

## Technical approach

Prefer Blender Python for repeatable scene construction and data import.

Manual Blender work is acceptable for art direction and mesh/material refinement, but measurements and important transforms should remain recoverable from source data or configuration.

Use meters throughout.

Current local scene convention:

- +X: local east / image horizontal reference
- +Y: local north / image vertical reference
- +Z: up from the seabed
- origin: arbitrary local wreck-site reference during graybox; replace with a documented geodetic/local tangent frame during the site pass

The initial camera is near nadir and approximately 4,023 m above the local seabed.

## Accuracy hierarchy

When effort or evidence is limited, prioritize:

1. camera altitude and perspective projection
2. metric scale
3. relative bow/stern placement and orientation
4. debris-field footprint
5. large-scale seabed shape
6. recognizable wreck silhouettes
7. material/lighting fidelity
8. fine wreck detail

At the final viewpoint, details below the image's useful spatial resolution do not deserve disproportionate effort.

## Workflow

### Phase 1 — truth / graybox

Goal: determine whether the honest geometry has the intended emotional effect.

Use:

- crude wreck proxies
- provisional low-frequency terrain
- approximate debris footprint
- fixed perspective camera
- simple directional lighting

Do not chase photorealism.

### Phase 2 — site reconstruction

Replace assumptions with sourced data:

- bathymetry / DEM
- georeferenced wreck-site maps
- measured bow/stern positions and orientations
- major debris concentrations
- visible large seafloor disturbances

Keep raw source data outside Git unless small and legally redistributable.

### Phase 3 — mood / final image

Only after geometry is trustworthy:

- terrain and wreck materials
- physically coherent low-angle illumination
- restrained haze / atmospheric perspective if useful
- negative space
- high-resolution render
- compositional refinement

Do not use fog, bloom, contrast, or grading to hide bad geometry.

## Repository rules

- Keep generated files under `build/` or other ignored working directories.
- Do not commit large bathymetry, point-cloud, photogrammetry, or scan datasets by default.
- Do not commit `.blend1` / backup files.
- Keep external dataset provenance documented under `data/`.
- Prefer small text configuration files over hard-coded unexplained constants.
- If a Blender script changes a visual assumption, update the relevant documentation/config in the same change.
- Preserve deterministic seeds for procedural graybox content unless randomness is the subject of an experiment.

## Blender automation

The first reproducible entry point is:

```bash
blender --background --python scripts/bootstrap_scene.py
```

It should:

1. clear the startup scene;
2. use metric units;
3. construct provisional terrain;
4. create bow/stern proxies;
5. create a deterministic debris proxy field;
6. position the camera at the configured altitude;
7. add simple illumination;
8. save a `.blend` file;
9. render a still image.

Keep this bootstrap script working while the project is in the graybox stage.

## Visual constraints

The final image should not resemble a heroic ship portrait.

Avoid:

- framing that fills the image with the wreck;
- theatrical spotlights aimed only at Titanic;
- exaggerated terrain relief;
- giant readable individual debris objects that should be sub-pixel at the chosen altitude;
- arbitrary camera tilt chosen only to make the ship look bigger;
- visual clutter that removes the abyssal emptiness.

Desired qualities:

- vast negative space;
- a small broken wreck;
- obvious separation between bow and stern;
- a debris field that makes the breakup spatially legible;
- terrain relief revealed more by light than by exaggeration;
- silence, isolation, depth, and archaeological rather than cinematic spectacle.

## Mathematical sanity checks

For an object of characteristic size `s` viewed from distance `h`, its approximate angular size is:

```text
theta = 2 * atan(s / (2h))
```

For a horizontal camera field of view `phi` at altitude `h`, approximate ground width at the target plane is:

```text
width = 2 * h * tan(phi / 2)
```

Use these relationships when evaluating whether an object should be visible or how many pixels it should occupy.

If an artistic choice contradicts the projection math, call it out rather than quietly making the choice.

## Definition of success for the first milestone

A deliberately ugly graybox render succeeds if it makes the viewer understand, without scale cheating, that the Titanic wreck is a tiny broken artifact spread across a broad patch of seabed nearly four kilometers below the ocean surface.

If the graybox does not work emotionally, change the composition and lighting before increasing model detail.
