# Source register

Add sources here when they become part of the reconstruction.

| ID | Source | What we use it for | CRS / units | Resolution | License / redistribution | Notes |
|---|---|---|---|---|---|---|
| _none yet_ | | | | | | |

## Audited candidates (not adopted)

These entries have been inspected, but they do not yet support any evidence-based
scene value. Detailed observations and checksums are in
[`SOURCE_AUDIT_2026-09-28.md`](SOURCE_AUDIT_2026-09-28.md).

| ID | Candidate | Possible role | Native coordinates / values | Effective resolution | Access / constraints | Audit status |
|---|---|---|---|---|---|---|
| `CAND-NOAA-2004-RAW` | [NOAA/NCEI `titanic2004` multibeam collection](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.multibeam:titanic2004_Multibeam) | Reprocess shipboard soundings into defensible broad terrain | WGS 84 navigation; per-beam depths in metres, positive down; vertical reference unresolved | Irregular soundings, up to 151 beams per ping in the audited sample | Electronic download; cite NOAA; raw, not NOAA QA/QC, not for navigation | Representative raw file decoded successfully; full archive not yet downloaded or gridded |
| `CAND-NOAA-2004-MOSAIC` | [NOAA multibeam mosaic ImageServer](https://gis.ngdc.noaa.gov/arcgis/rest/services/multibeam_mosaics/multibeam_mosaic_subsets/ImageServer) record `titanic2004_RAW_SB2112_w` | Low-frequency seabed shape only | EPSG:4326; one `float32` band; negative depth/elevation values; vertical reference unresolved | 3 arc-seconds, about 69 x 93 m at the site | Server permits copy and analysis; source collection limitations still apply | Native-resolution crop audited; contains seams/no-data and a four-cell extreme artifact, so direct mesh import is rejected pending QC |
| `REF-NOAA-2010-JPEG` | [NOAA 2010 expedition results](https://sanctuaries.noaa.gov/maritime/titanic/expedition_results.html) publication JPEGs | Visual reference for coverage and feature vocabulary | Coverage graphic prints WGS 84 / UTM zone 22N, but neither JPEG embeds georeferencing | 213 x 253 and 800 x 1036 display pixels | Credited to RMS Titanic, Inc. / WHOI AIVL; redistribution rights not established | Reference only; unsuitable as a height field or coordinate authority |
| `TARGET-WHOI-2010-GIS` | Reported 2010 sonar, optical mosaics, and GIS | Desired source for wreck/debris placement and local texture | NOAA reports GPS-positioned features; exact CRS, transforms, and vertical model not audited | Reported at several resolutions, from wide-area sonar to close optical work | No public raw/GIS download located; published imagery is copyrighted and licensing/contact may be required | Existence confirmed; data package and reuse terms unavailable |

## Measurement log

When a coordinate, dimension, heading, terrain feature, or debris boundary is derived from a source, record the derivation below.

### Template

- **Quantity:**
- **Value:**
- **Source ID:**
- **Method:** measured / transcribed / inferred / estimated
- **Uncertainty:**
- **Notes:**
