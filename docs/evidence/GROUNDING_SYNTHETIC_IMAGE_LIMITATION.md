# Grounding Paraphrase / Contrast Proof

Input: `data\demo\optical_after.tif`

| Query | Status | Task | Boxes | Decision |
|---|---|---|---:|---|
| Locate the surface water. | complete | GROUNDING | 1 | ANSWERED |
| Where is the water body in this image? | complete | GROUNDING | 1 | ANSWERED |
| Highlight regions containing water. | complete | GROUNDING | 1 | ANSWERED |
| Locate buildings in this image. | complete | GROUNDING | 1 | ANSWERED |

Mean IoU among water paraphrases: **1.0**
Water-vs-buildings first-box IoU: **1.0**

Same-concept paraphrases should be spatially consistent when evidence exists; a semantically different query should be allowed to return a different region or no region.