# Automatic Input Normalization

SatQuery inspects input content, attempts safe preprocessing, verifies the common grid and valid overlap, and then executes analysis. Originals are never overwritten. Inspection and execution share `gateway.validation.validate`; the inspector accepts an optional `query` for task-specific spectral requirements.

## Status and capabilities

- **READY**: compatible inputs without detected limitations.
- **READY_WITH_PREPROCESSING**: automatic normalization completed and verified. Read accompanying warnings and capability flags; preprocessing does not certify metadata or answer accuracy.
- **READY_WITH_LIMITATIONS**: usable input with disabled or uncertain capabilities, without a required normalization operation.
- **INCOMPATIBLE**: a structured blocking error with actionable guidance.

If preprocessing and limitations coexist, the preprocessing status is shown with `has_limitations`, warnings and explicit disabled capabilities. Input quality describes readability; it is not model confidence, evidence coverage, consensus, or final trust. Existing LOW_TRUST and refusal gates remain in force.

## Safe fixes

Temporal observations use the first/before image's CRS and grid. Optical/SAR fusion uses the optical reference without changing input IDs or user order. Valid CRS, affine, resolution and dimension differences use Rasterio reprojection. Nearest-neighbor sampling preserves sample ranges and avoids averaging logarithmic SAR power or unknown categorical values. No CRS is invented.

Known common temporal bands are mapped into reference order. Red/green/blue aliases are case-insensitive; numeric identifiers such as B4 require supporting sensor metadata because numbering is sensor-dependent. Additional bands are excluded with an explicit warning when they are not common to all observations. Requested NDVI/NDWI/NDBI require their bands on every date; missing bands disable that measurement, while visual tasks remain available.

At least 20% of reference pixels must be valid across every observation and every selected comparison band. Nonshared pixels become nodata on **all** dates, preventing them from being counted as change. Temporal outputs retain the reference dimensions for overlays. Optical/SAR outputs crop to the shared bounding window and retain nodata holes. The audit records overlap pixels/fractions and original/processed extent.

## Visual-only mode

Ordinary PNG/JPG/JPEG and unreferenced TIFF support available visual VQA, captions, pixel grounding and pixel-space measurements without benchmark provenance. Geographic coordinates, distances, hectares, km² and GIS exports require trustworthy georeferencing. Synthetic 0..1 bounds, impossible geographic bounds and degenerate transforms cannot authorize physical measurements. Plausible metadata alone does not establish survey accuracy; source provenance remains visible.

Visual temporal pairs need sufficient texture and a reliable translation diagnostic. Aspect-ratio changes over 2% or scale changes outside 0.5–2× are rejected. Translation is bounded using image size (3–10 pixels), uncovered edges become nodata, and residual alignment is verified. Registration scores and peak-to-sidelobe ratios are diagnostics, not calibrated probabilities. No nonrigid warp is applied. Declared benchmark pairs retain source pixels when bounded overlap diagnostics support the declaration; residual uncertainty stays visible. Unrelated or unstable images are rejected even if the user ticks the alignment declaration.

## Uncalibrated SAR mode

Unknown units remain UNKNOWN. Relative intensity/texture summaries and labeled proxy fusion can proceed. Calibrated backscatter, dB thresholds and sigma0/gamma0 claims remain unavailable. Declared db/linear units retain their existing provenance and scientific restrictions. Temporal pairs with differing SAR unit states currently require consistent units; SatQuery does not compare their raw values as though equivalent.

## Derivatives and audit

The canonical image dictionary now includes original metadata, working/source paths internally, normalization flags, warnings, geospatial capability flags, SAR unit status and preprocessing steps. Existing image IDs and APIs remain compatible.

Inspection verifies arrays in memory under the same processing semaphore as jobs. Execution writes derivatives to `data/uploads/<job-id>/normalized/imgN.tif`; specialist services and previews use these files. Derivatives store scaled float32 samples with identity scale/offset and NaN nodata, avoiding integer overflow and double application of source scales. Source dtype, nodata, scales, tags, dates and descriptions remain in `original_metadata`. Descriptions, general tags, band tags and color interpretation are preserved in derivatives where applicable. Public reports expose file names and hashes, not local filesystem paths.

Every transformation appears in `automatic_preprocessing` trace events, JSON input validation and HTML input metadata. Failed jobs clean their internal derivatives under the existing upload cleanup policy. Successful derivatives follow the existing retained-upload/report lifecycle so history and ROI follow-ups continue to work. The deployment currently has no automatic expiration policy for successful uploads; operators should retain or remove job artifacts together.

## Configuration

Environment defaults (also exposed by `GET /api/config`):

```dotenv
SATQUERY_MAX_UPLOADS=20
SATQUERY_MAX_UPLOAD_MB=128
SATQUERY_MAX_QUERY_CHARS=8000
SATQUERY_MAX_MULTIDATE=20
SATQUERY_MAX_DECODED_MB=1024
SATQUERY_AUTO_REPROJECT=1
SATQUERY_AUTO_RESAMPLE=1
SATQUERY_AUTO_BAND_REORDER=1
SATQUERY_AUTO_COREGISTER=1
```

Multi-date count is capped by the total upload limit. Large sequences warn about latency. Queries are trimmed, never truncated by the API. File size, query size, count and preprocessing failures have stable structured codes. Existing per-image limits of 16 million pixels/16 bands remain; decoded-job and reference-grid budgets are checked before allocating normalization outputs. Rasterio warps one band at a time with 64 MiB warp memory and one thread. The current specialists still require bounded arrays in memory; this is not an arbitrary-size streaming GIS engine.

The bundled Nginx request ceiling is 2600 MiB, sufficient for twenty 128 MiB uploads plus multipart overhead. If increasing deployment limits above that aggregate, update this proxy ceiling too. Per-file and count enforcement remains in the gateway.

## Intentional boundaries

No invented CRS, dates, sensor identity, calibration, Cartosat/RISAT validation or accuracy. No repair of corrupt imagery, zero overlap, optical/SAR temporal modality mismatch, unknown required spectral identities, or unstable registration. Placeholder georeferencing permits pixel use but never physical area. Missing sensor metadata alone does not prove an otherwise plausible geotransform is false. Benchmark scores are not rerun or edited by normalization changes.
