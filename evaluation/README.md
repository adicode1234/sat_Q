# SatQuery Evaluation

The production evaluation harness runs through SatQuery's controller/verification path, enforces explicit held-out splits, hashes images to detect train/evaluation overlap where training manifests are available, stores model modes/provenance and writes JSON artifacts.

## Current promoted artifact

- File: `evaluation/results.json`
- Status: `PARTIAL`
- Scope: `SMALL PUBLIC-DATA SMOKE EVALUATION; not full benchmark reproduction`
- Completed examples: `72`
- Macro exact match: `0.4375`
- Sample-weighted exact match: `0.3333333333333333`
- Official full-suite complete: `False`

### Per dataset

- VRSBench: requested=4, completed=4, failed=0, exact_match=0.25, token_f1=0.25, splits=['official_eval']
- RSVQA: requested=64, completed=64, failed=0, exact_match=0.3125, token_f1=0.3125, splits=['official_test']
- CDVQA: requested=4, completed=4, failed=0, exact_match=0.75, token_f1=0.75, splits=['test_mirror']

## Interpretation

These numbers are valid for the local held-out/public slices represented by the manifest. They are **not** a claim of full official benchmark reproduction unless the manifest is replaced by the complete official suites and `official_test_suite_complete` is truthfully set by the evaluation logic.
