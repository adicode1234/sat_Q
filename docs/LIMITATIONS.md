# SatQuery AI — Known Limitations

Last updated: 2026-09-12

## Benchmark scope

The currently promoted evaluation artifact contains **72** completed examples and reports `status=PARTIAL` with scope: **SMALL PUBLIC-DATA SMOKE EVALUATION; not full benchmark reproduction**.

- Macro-average exact match across available dataset slices: **0.4375**
- Sample-weighted exact match across the promoted artifact: **0.3333333333333333**
- `official_test_suite_complete`: **False**

These values are bounded local evaluation results, not a full official leaderboard reproduction.

## Model quality

Single-image VQA remains the main model-quality weakness. Change-VQA results are promising but based on a small CDVQA slice. Do not present either as statistically conclusive.

## Real-domain validation

SatQuery supports real GeoTIFF/TIFF ingestion and co-registration checks. A public Sentinel-1/Sentinel-2 proxy run may be recorded in `REAL_WORLD_PROXY_TEST.md`. This must not be relabeled as Cartosat-2S/RISAT validation.

## Cartosat-2S / RISAT

No genuine organizer/authorized Cartosat-2S/RISAT evaluation result is available in this repository. Generalization to that hidden target domain remains an external evaluation boundary.

## Reports / GIS

JSON, HTML, and GeoJSON outputs are implemented. Shapefile/GeoPackage/PDF must not be claimed unless separately demonstrated.

## Confidence

Trust/evidence scores are decision-support signals, not calibrated probabilities of factual correctness. Low evidence can correctly lead to refusal or qualified output.
