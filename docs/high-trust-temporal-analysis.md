# High-trust temporal analysis

SatQuery's temporal result is an evidence-derived trust score, not a guaranteed probability of correctness. Generic before/after questions use a composite workflow: validation and normalization, alignment diagnostics, deterministic candidate appearance change, Change-VQA as an auxiliary suggestion, before/after grounding, measurements, claim verification, consensus, and safety gates.

## Evidence boundaries

The deterministic change mask can support the limited claim that visible appearance changed between comparable observations. Its changed-pixel fraction is a measurement, not a probability and not semantic ground truth. A semantic claim such as river shrinkage requires independent localization and comparison of the relevant before and after regions. Grounding is evidence for spatial localization, never ground truth.

RGB imagery can support visual and relative pixel-area comparisons. Vegetation or water spectral conclusions require the relevant named bands. Physical area requires trusted georeferencing; visual-only alignment permits pixel evidence but not geographic area. Missing evidence is reported as unavailable, not as negative evidence.

## Trust policy

Claims are atomic and receive separate verification statuses: `SUPPORTED`, `UNVERIFIED`, `CONFLICTED`, or `UNSUPPORTED`. Poor alignment caps trust, warning alignment limits the score, and conflicting methods are exposed rather than averaged away. High trust is permitted only when suitable inputs, strong evidence, adequate coverage, and agreement support the same limited claim.

The current model score is explicitly uncalibrated. No confidence multiplication or hard-coded target score is used. Calibration requires a held-out labeled split and will be added only when that data exists; until then model confidence remains auxiliary metadata.

## Reports and limitations

JSON and HTML reports expose `temporal_evidence`, before/after grounding, atomic `checks`, `evidence_support`, `verification_coverage`, alignment quality, consensus, trust explanation, and limitations. High trust precision, rather than the number of high-trust results, is the appropriate future evaluation target. Seasonal effects, illumination, registration residuals, pretrained grounding errors, and the small Change-VQA training scope remain scientific limitations.