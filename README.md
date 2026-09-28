# Titanic — Drained Atlantic

A single-image visualization of the RMS Titanic wreck site as it might appear if the North Atlantic were removed and the viewer were suspended roughly **2.5 miles / 4,023 m above the seabed**.

The point is not to make Titanic look impressive.

The point is to make it look **disturbingly small**.

From roughly the altitude of the present ocean surface, the bow, stern, and debris field should read as a broken, decaying trace on an immense dark seabed. The image should preserve the real scale relationships closely enough that its emotional effect comes from the geometry rather than from exaggeration.

## Prime directive

**Build the truth first; then make the truth beautiful.**

Do not enlarge the wreck, compress distances, narrow the debris field, lower the camera, or vertically exaggerate the site merely to make the subject easier to see.

We may improve legibility with lighting, materials, contrast, resolution, and composition. We should not falsify the scale that gives the image its meaning.

## Deliverable

One still image.

There is intentionally no requirement for:

- navigation
- animation
- real-time rendering
- collision
- gameplay
- arbitrary viewpoints
- a complete high-resolution digital twin

The scene only needs to be convincing and approximately correct from the chosen camera.

## Working model

Treat this primarily as a measured diorama photographed in Blender:

```text
public bathymetry / wreck-site maps
             ↓
      local metric frame
             ↓
 terrain + bow + stern + major debris
             ↓
   fixed perspective camera
        z ≈ 4,023 m
             ↓
         still render
```

The coordinate system is more important than fine mesh detail.

## Phases

### 1. Truth pass — graybox

Prove the composition using deliberately crude geometry:

- metric scene
- provisional seabed
- bow proxy
- stern proxy
- approximate debris footprint
- fixed camera at 4,023 m above the local seabed
- perspective projection
- simple directional light

The first question is not “does it look like Titanic?”

It is:

> Does an honestly scaled wreck site viewed from this altitude already feel tiny, isolated, and unsettling?

### 2. Site pass — geometry and archaeology

Replace the graybox assumptions with better evidence:

- public bathymetry / DEM
- georeferenced wreck-site maps
- bow and stern position/orientation
- major debris concentrations
- large seafloor features and impact disturbances

The goal is approximate archaeological honesty at the spatial frequencies visible from ~4 km away.

### 3. Mood pass — image making

Only after geometry is locked:

- physically plausible low-angle lighting
- terrain/wreck materials
- restrained atmospheric perspective if useful
- long shadows to reveal relief
- carefully controlled contrast
- large amounts of negative space
- high-resolution final render

Fine detail matters only where it survives the final angular resolution.

## Repository layout

```text
.
├── AGENTS.md                # instructions for Codex/agents
├── README.md                # project overview
├── config/
│   └── graybox.json         # provisional scene measurements
├── data/
│   └── README.md            # where external/source datasets belong
├── docs/
│   ├── geometry.md          # coordinate/camera conventions and math
│   └── vision.md            # artistic intent and non-negotiables
└── scripts/
    └── bootstrap_scene.py   # reproducible Blender graybox generator
```

Generated Blender files, renders, caches, and large source datasets should not be committed unless there is a specific reason.

## First run

Install Blender, clone the repository, and from the repository root run Blender's executable against the bootstrap script.

Windows example:

```powershell
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python scripts/bootstrap_scene.py
```

macOS example:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/bootstrap_scene.py
```

Linux example:

```bash
blender --background --python scripts/bootstrap_scene.py
```

The script creates:

```text
build/titanic-graybox.blend
build/titanic-graybox.png
```

You can also open Blender normally and run `scripts/bootstrap_scene.py` from the Scripting workspace.

## The graybox is intentionally provisional

The values in `config/graybox.json` are scaffolding, not claims of archaeological precision. In particular, bow/stern proxy dimensions, their exact relative coordinates, terrain relief, and debris footprint must eventually be replaced or justified from sources.

The one quantity we intentionally establish immediately is the viewing scale: approximately **4,023 m above the seabed**.

## Accuracy hierarchy

When tradeoffs are necessary, prefer:

1. camera altitude / projection
2. scene scale
3. relative wreck-piece placement
4. debris-field extent
5. large terrain geometry
6. recognizable wreck silhouettes
7. materials and lighting
8. small wreck detail

A beautifully modeled davit in the wrong geometry is useless here.

## Design test

At any point ask:

> If the viewer did not know the dimensions, would the image still make them understand that Titanic fell through nearly four kilometers of ocean and came apart across a surprisingly broad patch of abyssal floor?

If yes, we are building the right image.
