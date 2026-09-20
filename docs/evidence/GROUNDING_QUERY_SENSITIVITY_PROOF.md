# Grounding Query-Sensitivity Proof

Dataset: **VRSBench**

Image: `data\vrsbench\P0003_0002.png`

## Queries

| Query | Status | Boxes |
|---|---|---:|
| Locate the water. | complete | 1 |
| Where is the water body? | complete | 1 |
| Highlight the surface water. | complete | 1 |
| Locate the buildings. | complete | 2 |
| Locate the road. | complete | 1 |
| Locate the forest. | complete | 0 |

## Spatial consistency

Mean IoU among water paraphrases: **0.9831632223704933**

Water vs semantic contrast IoUs: `{'building': 0.0, 'road': 0.9957264957264957}`

## Conclusion

Grounding is text-conditioned: semantically different prompts produced different spatial predictions.

The earlier synthetic demo GeoTIFF produced whole-image detections and is therefore not used as evidence of grounding quality.