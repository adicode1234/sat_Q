---
name: Satellite Change Analysis Output Rules
description: Rules for generating satellite change analysis output
trigger: always_on
---

# RULES FOR SATELLITE CHANGE ANALYSIS OUTPUT:

1. **SINGLE SOURCE OF TRUTH:** Any percentage or area value (e.g., River Channel %, Vegetation %) must be computed ONCE and reused everywhere in the output — in the map label, the summary text, and the variance matrix. NEVER recompute or restate the same metric with a different number in two different places.

2. **CONFIDENCE MUST BE CONSISTENT:** There is exactly ONE overall confidence score per analysis. If overall confidence is X%, no sub-component (e.g., "Trust Verification") may claim a higher or contradicting confidence label like "High Confidence" unless X% itself is >70%. If confidence is low (<50%), all claims must be hedged ("possible", "estimated", "approximate") — never state absolute claims like "0.0% displacement" or "zero breaches" at low confidence.

3. **NO FABRICATED PRECISION:** Do not output pixel coordinates, hectare values, or meter measurements UNLESS they are derived from actual georeferenced raster data with a known ground sample distance (GSD) and pixel-to-area conversion. If true geospatial calculation is not available, output qualitative direction only ("water extent increased") — do NOT invent decimal-precision numbers to sound authoritative.

4. **INTERNAL CONSISTENCY CHECK BEFORE OUTPUT:** Before finalizing, verify that every "Before → After" delta in the matrix logically matches its own tag/label. E.g., if Before=5.0% and After=32.6%, the tag CANNOT say "Stable" or "0.0% change" — it must say something like "+27.6pp increase". Flag any tag/value mismatch as an error rather than emitting it.

5. **IF UNCERTAIN, SAY SO EXPLICITLY:** Confidence score should reflect genuine model uncertainty. Do not pad the report with fake-precise numbers to compensate for a low confidence score.
