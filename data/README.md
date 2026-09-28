# Data

This directory is for documentation and small redistributable inputs.

Large external datasets should normally remain local and are ignored under:

```text
data/raw/
data/processed/
```

Examples may eventually include bathymetry, DEM rasters, georeferenced wreck-site imagery, point clouds, or derived meshes.

## Provenance rule

For every dataset used to move a scene value from “graybox assumption” to “evidence-based,” record:

- source organization / author;
- dataset or map title;
- URL or stable identifier;
- acquisition/publication date if known;
- coordinate reference system;
- native units/resolution;
- license or redistribution constraints;
- which scene values were derived from it;
- any manual interpretation or uncertainty.

Do not commit third-party data simply because it was downloadable.

## Suggested local layout

```text
data/
├── README.md
├── SOURCES.md
├── raw/          # downloaded originals; gitignored
└── processed/    # converted/cropped/derived working data; gitignored
```

The Git history should preserve our reasoning and transforms even when the underlying large files remain local.
