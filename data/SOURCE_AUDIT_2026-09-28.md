# Titanic wreck-site source audit — 2026-09-28

## Decision boundary

This is an acquisition and format audit, not a source-selection decision.

- No candidate below is adopted as scene truth.
- No camera, wreck, debris, terrain, or coordinate value was changed.
- Downloaded originals and derived audit files remain under Git-ignored
  `data/raw/` and `data/processed/`.
- The audit used a minimum representative download rather than mirroring the
  complete sonar archive.

## Outcome

| Candidate | What it actually is | Useful now? | Principal blocker |
|---|---|---|---|
| NOAA 2004 raw multibeam | Gzip-compressed, big-endian L3/SeaBeam XSE event streams (`MB-System` format 94) containing navigation, motion, sound-velocity, sidescan, and multibeam groups | Yes, as the best accessible source from which to regenerate broad bathymetry | Full archive processing and QC are still required; NOAA labels it raw and not subjected to NOAA QA/QC |
| NOAA 2004 ImageServer mosaic | A one-band `float32` GeoTIFF depth grid in EPSG:4326 | Provisionally, for low-frequency terrain experiments after artifact masking | Roughly 69 x 93 m cells and visible mosaic artifacts; far too coarse for the wreck or debris field |
| NOAA 2010 public images | Flattened RGB JPEG publication graphics | Reference only | No embedded georeference or numeric depths; copyright/reuse not established |
| Reported WHOI/RMST 2010 GIS | Georectified multi-resolution sonar/optical products and positioned features, according to NOAA/WHOI descriptions | Potentially the most relevant site source | No public raw raster/vector/GIS package was located in the audited pages; access and licensing are unresolved |

## 1. NOAA/NCEI 2004 raw multibeam

Source landing page:

<https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.multibeam:titanic2004_Multibeam>

NOAA identifies the collection as SeaBeam 2112 data distributed as
`MBF_L3XSERAW`, plus sound-speed profiles and XML metadata. The landing page
states EPSG:4326 for the horizontal reference, marks the vertical datum
unknown, and warns that the raw data has not been through NOAA QA/QC and is not
for navigation.

MB-System identifies format 94 as the L3/ELAC/SeaBeam XSE binary format:

<https://www.ldeo.columbia.edu/res/pi/MB-System/mbweb/formatdoc/>

### Representative download

| File | Bytes | SHA-256 |
|---|---:|---|
| `sb200405310854.mb94.gz` | 7,463,511 | `4EFE5CBDA57BD3A7D608D5ADE45F1C2A9F3D79CDCCFF342207B6370EB8E27C28` |
| `svp.tar.gz` | 58,352 | `1F68677A3B866BD4AFE0960A55C0AC802F64CA4A6B149744D8C06995EF53DBAB` |
| `Titanic2004_COLLECTION_LEVEL_RESOLVED.xml` | 64,622 | `A3DF7B081A41C7E0EA2BDEACF762204FAC876561292B6C7312B4CF07A0CC7938` |
| `titanic2004_Multibeam.xml` | 84,371 | `428E716C5C6311E52343B8B5079C598372C6FB7F445AFAA9DAB06A03E6DBD9BF` |

### Binary structure observed

The gzip member expands to 17,199,092 bytes. A structural parser consumed the
entire stream without a framing error. XSE stores `$HSF` frames containing
`$HSG` groups; integers and floating-point values in this file are big-endian.

The file spans `2004-05-31T08:49:26.314300Z` through
`2004-05-31T09:27:43.149000Z` and contains:

| Frame type | Count | Relevant content observed |
|---|---:|---|
| Navigation | 1,023 | WGS 84 position, accuracy, motion, heading, and GPS groups |
| Sound velocity | 1,359 | Depth, velocity, conductivity, salinity, and temperature groups |
| Sidescan | 200 | General, amplitude, and weighting groups |
| Multibeam | 200 | Travel time, quality, amplitude, delay, across/along-track position, depth, angle, heave, roll, pitch, gates, noise, and receive-heave groups |
| SeaBeam vendor data | 799 | SeaBeam-specific setup/measurement groups |

Navigation positions cover longitude `-49.966750` to `-49.873733` and latitude
`41.728233` to `41.733200`. This is a single narrow survey segment, not the
collection extent.

Each of the 200 multibeam records contains 151 depth, amplitude, and quality
values: 30,200 beam observations total. MB-System maps quality code `1` to a
valid beam and code `8` to null. The audited file contains 23,908 valid beams
(`79.1656%`). Valid depths are positive-down metres:

```text
minimum      3553.374 m
1st pct.     3685.124 m
median       3776.476 m
99th pct.    3891.741 m
maximum      3985.987 m
```

The `svp.tar.gz` archive contains one two-column depth/sound-speed profile and
112 `.ssv` operational profile logs. These values correct acoustic travel time
for the changing speed of sound through the water column; they are processing
inputs, not terrain geometry themselves.

### Interpretation

Observed: the raw file contains real numeric soundings and the sensor/navigation
context needed to grid them. It is not a picture or a ready-to-import heightmap.

Recommendation: retain this collection as the accessible authoritative input
for broad terrain. If adopted, process the complete relevant survey subset with
MB-System or an equivalently validated decoder, preserve beam flags, and grid in
a metric local CRS. Do not write a one-off partial XSE decoder as the production
pipeline merely because the framing was easy to inspect.

## 2. NOAA 2004 ImageServer mosaic

Service:

<https://gis.ngdc.noaa.gov/arcgis/rest/services/multibeam_mosaics/multibeam_mosaic_subsets/ImageServer>

The audited service record is:

```text
Name          titanic2004_RAW_SB2112_w
SURVEY_NAME   titanic2004
DATASET_NAME  titanic2004_RAW_SB2112
DATA_TYPE     MB RAW
LowPS         0.0008333333335 degrees (3 arc-seconds)
```

The audit export deliberately requested the native 3-arc-second resolution,
nearest-neighbor resampling, the raw raster function, and only the
`titanic2004` record:

```text
bounds      -50.010, 41.680, -49.890, 41.770
dimensions  144 x 108
band        1 x float32
CRS         EPSG:4326
nodata      -99999
cell size   0.000833333 degrees
```

At the crop centre, that is approximately `69.2 x 92.8 m` per cell. The file
contains 15,505 valid cells out of 15,552 (`99.698%`). Depth/elevation values
are negative:

```text
minimum      -3926.427 m
1st pct.     -3884.448 m
median       -3785.098 m
99th pct.    -3706.438 m
maximum      -3001.413 m
```

File:

```text
data/processed/audit/titanic2004-noaa-mosaic-native-audit.tif
bytes    131,914
SHA-256  B50DCE415562DAB2A720FE550CE7B97D80B7BF66306973072C26EF8A91B8EC04
```

### Important defects and ambiguities

1. Four adjacent cells near `-49.9175, 41.7200` jump to approximately
   `-3002 m`, about 700–900 m away from surrounding values. A four-cell cliff of
   that magnitude is inconsistent with the surrounding grid and is treated as
   a mosaic artifact unless independently corroborated.
2. The preview exposes additional seams, holes, and line-oriented texture that
   require QC before any mesh import.
3. The GeoTIFF contains no band-unit tag. Collection metadata says "Vertical
   Datum: Unknown", while another XML extent link labels depths as metres
   relative to MSL. That conflict leaves the vertical reference unresolved.
4. At the current 90-degree, 2,560-pixel render, one source cell spans roughly
   22 x 30 image pixels. Interpolation can make it smooth, not more detailed.

An earlier 1,024 x 768 export request oversampled the service and produced a
larger interpolation/overview artifact. It is rejected. Requesting more pixels
from a coarse image service does not create more terrain information.

### Interpretation

Observed: this is a genuine coordinate-aware numeric raster and can drive a
Blender displacement mesh after projection, sign normalization, artifact
masking, and gap handling.

Recommendation: use it only as a rapid low-frequency terrain experiment. It
cannot locate or model the bow, stern, debris, impact scars, or small seabed
contours. Prefer a freshly gridded product from the raw soundings if the audit
continues to support that path.

## 3. NOAA/WHOI 2010 public material

NOAA describes the 2010 result as a multi-resolution sonar map augmented by
GPS-positioned features and detailed optical mosaics:

<https://sanctuaries.noaa.gov/maritime/titanic/expedition_results.html>

WHOI describes an initial `3 x 5 nautical mile` sidescan survey, a tighter
down-looking survey, and more than 250 optical mosaics:

<https://www.whoi.edu/press-room/news-release/whoi-team-uses-advanced-imaging-data-to-bring-a-new-view-of-titanic-to-the-world/>

### Public files inspected

| File | Pixels | Embedded metadata | SHA-256 |
|---|---:|---|---|
| `er2-bow-sonar-map.jpg` | 213 x 253 RGB | No EXIF or spatial metadata | `6550730FDA54CC4D9759380481D873F653E04AE96721455EFB35345DF1E5A710` |
| `er3-remus-sidescan-coverage.jpg` | 800 x 1036 RGB | No EXIF or spatial metadata | `1D725B2D7F97D7D08FE077C1FB455391297D154A58B63C862C77FD13D9BDA8F0` |

The larger coverage graphic visibly prints `WGS 1984 UTM Zone 22N`, metre
units, a grid, and a scale bar. Those are flattened pixels, not embedded control
points or a GeoTIFF transform. Manual georeferencing might produce an
approximate reference layer, but it would not recover numeric elevation and
would require reuse permission.

The audited NOAA and WHOI pages did not expose a downloadable raw sonar,
GeoTIFF, shapefile, or geodatabase package for the 2010 GIS. This is not proof
that no such distribution exists; it means access was not established by this
audit.

## Recommendation before scene import

Do not yet project imagery into Blender as though all pixels were seabed height.
The sources separate into different data roles:

```text
raw multibeam beams -> QC/gridding -> low-frequency terrain height
2010 sidescan       -> georeferenced intensity/texture, if obtainable
2010 GIS features   -> wreck/debris positions, if obtainable
optical mosaics     -> local appearance/reference, subject to licensing
```

The next small semantic batch should be one of:

1. **Access-first (recommended):** contact NOAA/WHOI/RMST for the 2010 GIS or a
   licensed georeferenced export, because it best addresses wreck and debris
   placement.
2. **Terrain-first:** download only the 2004 raw files intersecting the intended
   9 x 9 km work area, process them with MB-System, and compare the resulting
   grid against the NOAA mosaic before creating a Blender mesh.

Both paths need a documented metric local frame before scene coordinates are
changed.
