import argparse, json, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);(root/'docs').mkdir(exist_ok=True);(root/'evaluation').mkdir(exist_ok=True)
bench=json.loads((root/'evaluation'/'results.json').read_text(encoding='utf-8')) if (root/'evaluation'/'results.json').exists() else {}; ds=bench.get('datasets',{}); completed=sum((x.get('completed') or 0) for x in ds.values()); macro=bench.get('combined_exact_match'); weighted_num=0; weighted_den=0
for x in ds.values():
    c=x.get('completed') or 0; em=x.get('exact_match')
    if em is not None: weighted_num+=c*em; weighted_den+=c
weighted=weighted_num/weighted_den if weighted_den else None

def w(path,text): path.write_text(text.strip()+"\n",encoding='utf-8')

w(root/'docs'/'ADAPTATION_JUSTIFICATION.md', '''# Remote-Sensing Adaptation Justification

SatQuery uses a VRSBench-based LoRA/ViLT adaptation path rather than claiming a full BigEarthNet reproduction. The project requirement permits remote-sensing adaptation using BigEarthNet **or other open-source training data**. VRSBench is directly aligned with remote-sensing vision-language tasks and therefore provides task-relevant supervision for visual question answering and language-conditioned analysis. This choice is a pragmatic task-aligned adaptation, not a claim that VRSBench and BigEarthNet are equivalent datasets.

Current limitation: adaptation is small-scale and does not establish production-level generalization to Cartosat-2S/RISAT imagery. Real-domain proxy evidence is tracked separately in `REAL_WORLD_PROXY_TEST.md`.
''')

w(root/'docs'/'LIMITATIONS.md', f'''# SatQuery AI — Known Limitations

Last updated: {time.strftime('%Y-%m-%d')}

## Benchmark scope

The currently promoted evaluation artifact contains **{completed}** completed examples and reports `status={bench.get('status')}` with scope: **{bench.get('scope')}**.

- Macro-average exact match across available dataset slices: **{macro}**
- Sample-weighted exact match across the promoted artifact: **{weighted}**
- `official_test_suite_complete`: **{bench.get('official_test_suite_complete')}**

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
''')

per='\n'.join(f"- {name}: requested={x.get('requested')}, completed={x.get('completed')}, failed={x.get('failed')}, exact_match={x.get('exact_match')}, token_f1={x.get('token_f1')}, splits={x.get('splits')}" for name,x in ds.items())
w(root/'evaluation'/'README.md', f'''# SatQuery Evaluation

The production evaluation harness runs through SatQuery's controller/verification path, enforces explicit held-out splits, hashes images to detect train/evaluation overlap where training manifests are available, stores model modes/provenance and writes JSON artifacts.

## Current promoted artifact

- File: `evaluation/results.json`
- Status: `{bench.get('status')}`
- Scope: `{bench.get('scope')}`
- Completed examples: `{completed}`
- Macro exact match: `{macro}`
- Sample-weighted exact match: `{weighted}`
- Official full-suite complete: `{bench.get('official_test_suite_complete')}`

### Per dataset

{per}

## Interpretation

These numbers are valid for the local held-out/public slices represented by the manifest. They are **not** a claim of full official benchmark reproduction unless the manifest is replaced by the complete official suites and `official_test_suite_complete` is truthfully set by the evaluation logic.
''')

real=root/'docs'/'REAL_WORLD_PROXY_TEST.md'
if not real.exists():
    w(real, '''# Real-World Optical/SAR Proxy Test

Status: **PENDING REAL-SENSOR PROXY RUN**

SatQuery's synthetic/demo GeoTIFF path is already verified. This document is reserved for a real Sentinel-1/Sentinel-2 proxy run.

Recommended source: SEN12MS / SEN12MS-CR, a public dataset of corresponding Sentinel-1 SAR and Sentinel-2 multispectral imagery. If a converted mirror is used, original product CRS/geotransform may not be preserved; that run therefore proves **real-sensor image-domain / cross-modal behavior with metadata limitations**, not complete operational geospatial provenance.

Do not claim Cartosat-2S/RISAT validation from this proxy.
''')
print('Wrote documentation artifacts.')
