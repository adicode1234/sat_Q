# Real imagery backend upgrade — 13 September 2026

The existing UI design is unchanged. The backend accepts compatible user uploads, with routing based on scenario, query, band names and radiometric metadata. It is not restricted to fixed demo images. This does not mean every sensor, raw product or question has a validated model.

## Completed

- Added three real-data-trained water experts: optical, SAR and joint optical/SAR. They run through the registry, validation, verification, consensus and reporting pipeline.
- Downloaded 144 Sen1Floods11 image/label triplets using the original official split files: 96 training, 24 validation and 24 test chips. Manifest contains source URLs and SHA-256 hashes.
- Trained each model for 1,000 CPU steps. Optical uses reflectance bands; SAR uses VV/VH backscatter and local texture; joint combines both. These are small supervised MLPs, not large pretrained segmentation transformers.
- Fitted temperature and water thresholds on validation data only. Stored before/after evidence. Test labels do not set live confidence.
- Added explicit reflectance conversion, scale/offset double-application checks, preserved natural RGB colors and persisted normalized derivatives for service consistency.
- Disabled synthetic land-cover/fusion/grounding fallbacks on real uploads.
- Distinguished missing verification from contradictory evidence. Physical checks use the model's actual valid-pixel domain. A temporal mask or its own grounding boxes cannot independently certify claims derived from them.
- Preserved usable deterministic measurements when neural semantic inference is unavailable.
- Rebuilt and restarted backend Docker services. Live health reports the real water checkpoints. Frontend container was not rebuilt or restarted.
- Passed 88 tests. Ran 72 full-pipeline real-data evaluations and three successful live HTTP uploads with preview, JSON and HTML report retrieval.

## Measured water results

On all 24 test chips, evaluated over valid reference labels aligned to each pipeline output grid:

- Optical: IoU 0.9109; F1 0.9534.
- SAR: IoU 0.6144; F1 0.7611.
- Joint: IoU 0.9006; F1 0.9477.

IoU measures overlap with labeled water masks; it is not an overall application accuracy score. Eight test chips were inspected during early development. The remaining 16 have separately reported results: optical IoU 0.9383, SAR 0.7151, joint 0.9328. These are subsets of the official benchmark, not its complete test split. Event locations can overlap across official chip splits; this is not geographic or sensor-transfer validation. Joint performance does not consistently exceed optical performance.

Evidence files: `evaluation/real_water_summary.json`, `evaluation/live_real_water_summary.json`, `training/water_before_after.json`, and `models/checkpoints/water_real/evaluation.json`.

## Compatible inputs

Water expert optical input requires named blue, green, red, NIR and SWIR bands and known reflectance scaling. The data used for training is Sentinel-2 L1C. Other sensors with these bands can run, but their accuracy is unvalidated. Ordinary RGB photos cannot supply missing infrared information.

The radar expert requires named VV and VH bands in declared calibrated dB or linear power. A single polarization, HH/HV, raw DN, amplitude, complex SLC or a SAR screenshot cannot silently be treated as this model's input. Available calibrated single-band measurements can still be returned. Raw SAR radiometric calibration needs the source product metadata and calibration LUT; changing a dropdown does not perform calibration.

Pairs need compatible spatial coverage; grid normalization and overlap cropping are recorded in the trace. Multi-date inputs still need correct acquisition dates. Appearance change is not proof of land-cover change or its cause.

The existing upload UI supports band mapping and SAR unit selection. For optical files, embedded raster scales/offsets or unambiguous quantification metadata are read automatically. If those are absent, the API accepts `sensor`, `reflectance_scale` and `reflectance_offset` in each image options object. Use source documentation to supply them; never guess from brightness or band count.

For the unchanged UI, `scripts/prepare_optical.py` creates a separate TIFF with explicitly supplied band names and raster scale/offset metadata. It preserves the original file and refuses to overwrite an existing destination. Example, from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_optical.py --input data/sen1floods11/Ghana_313799_S2Hand.tif --output data/my_tagged_optical.tif --bands coastal,blue,green,red,rededge1,rededge2,rededge3,nir,nir_narrow,water_vapor,cirrus,swir,swir2 --scale 0.0001
```

That scale and band order apply to this documented dataset, not arbitrary images. A prepared copy is already available at `data/real_upload_examples/Ghana_optical_tagged.tif`. Its matching radar file is `data/sen1floods11/Ghana_313799_S1Hand.tif`; choose SAR, band order `vv,vh`, and calibrated dB. Ask “What areas are covered by water?” Single uploads and co-registered pairs both work. These are examples only; the application does not identify filenames to choose results.

## Confidence and limitations

The water softmax is temperature-scaled on validation data. The exposed model score is conservatively bounded by validation IoU; this bound is a reliability heuristic, not probability calibration. Symbolic agreement compares the result with independent deterministic proxies. NDWI and low radar returns are themselves imperfect proxies; disagreement is retained, not suppressed to produce higher trust.

Low trust does not erase candidate masks or measurements. A higher score is not a guarantee. Cloud, snow, smooth dry ground, shadows, different acquisition conditions and sensor transfer can invalidate a confident prediction. Flood causation and object counts are not inferred from water coverage.

General VQA/captioning, buildings, vegetation semantics, grounding and semantic change have not received equivalent real-data training in this upgrade. ViLT remains a small remote-sensing adaptation with auxiliary suggestions; DINO remains pretrained; the existing change-VQA head has extremely limited training. NDVI/NDBI measurements and appearance-change masks remain available when inputs permit. Universal semantic analysis of arbitrary SAR/optical products is not complete or claimed.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m training.fetch_flood_data
.\.venv\Scripts\python.exe -m training.train_water
.\.venv\Scripts\python.exe -m evaluation.real_water
.\.venv\Scripts\python.exe -m evaluation.live_real_water
.\.venv\Scripts\python.exe -m pytest tests -q
```

For a backend-only container update:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ml.yml build gateway vqa grounding change fusion change-mask
docker compose -f docker-compose.yml -f docker-compose.ml.yml up -d --no-deps gateway vqa grounding change fusion change-mask
```

Dataset source and original documentation: https://github.com/cloudtostreet/Sen1Floods11. Follow its license and attribution when redistributing imagery.
