# Accuracy upgrade — 19 September 2026

## Changes deployed

- Restored actual SegFormer inference; replaced fixed colour-rule water scores with a labelled-data RGB classifier.
- Trained a 12-feature / 64-hidden-unit RGB water MLP on 96 Sen1Floods11 training chips (1,600 steps). Five-by-five RGB moments provide local texture. Validation-selected temperature, threshold and checkpoint.
- Continued optical, SAR and joint water training for 1,200 steps each. Only validation-improving optical and joint checkpoints promoted.
- Preserved VQA question meaning, raw model scores and negative answers. Counts and colour questions route to VQA rather than generic keyword grounding.
- Removed inflated 82–95% confidence, fabricated report percentages, invented geolocation from filenames, invented spectral ranges and risk claims, and frontend colour-rule overlays.
- Normal PNG/JPEG RGB is no longer brightened as if it were Sentinel reflectance.
- One segmentation drives composition, masks and scene text. Small water candidates are not automatically declared absent. Unknown measurements remain unavailable.

## Measured outcomes

| Model / method | Previous test IoU | Updated test IoU | Action |
|---|---:|---:|---|
| Optical water | 0.89667 | 0.90202 | Promoted |
| Optical + SAR water | 0.89595 | 0.90048 | Promoted |
| SAR water | 0.59385 | 0.59385 | Kept original |
| RGB colour rules → learned RGB water | 0.07358 | 0.44159 | Promoted |

Water expert comparisons use 20,000 sampled valid pixels per official test chip. RGB before/after compares 10,000 sampled valid pixels per chip on identical fixed RGB renderings. These are different protocols; do not compare RGB IoU directly with multispectral IoU. Validation selects weights and thresholds; test labels never train or select weights. Official chip splits can share events, so geographic independence and universal accuracy are not established.

ViLT LoRA: 64 continuation steps; no validation improvement, original retained. Only 16 training questions across six images exist. Change-VQA: 120 continuation steps, validation worsened; original retained. Only two labelled training image pairs exist. Their validation groups were excluded from continuation but had appeared in historical training; they are not independent generalization evidence.

Synthetic RGB adapter and synthetic fusion: exercised 300 steps each; originals retained. Synthetic scores do not establish real-world accuracy. Grounding DINO and multiclass SegFormer retain pretrained weights because no suitable object boxes / multiclass masks are available locally. Their water path now uses the separately trained RGB water expert. Measurement and change-mask tools are deterministic, not trainable models.

## Verification

98 backend tests passed, including new regression tests for question preservation, PNG scaling, nodata, small river components and fabricated geolocation. Frontend production build passed. Updated local API returned HTTP 200 for the bundled river image. Estimated water changed to 22.4%; this sample has no ground-truth mask, so that percentage is not an accuracy measurement. False positives remain visible, and overall evidence trust stays low (17.84%) instead of being artificially increased.

## Limits and next data required

RGB held-out IoU remains modest (~44%); do not claim 90% accuracy on JPEG uploads. Additional representative labelled RGB masks, object bounding boxes, VQA image/question/answer examples and many distinct before/after labelled image pairs are needed to establish broad improvements. No paid GPU job or external model training service was launched.

Training and comparison JSON files in `training/` and `evaluation/rgb_refinement_comparison.json` contain the detailed results. A pre-change backup is created in `.accuracy-backup/2026-09-19/` when installing this upgrade.
