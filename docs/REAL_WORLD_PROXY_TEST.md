# Real-World Optical/SAR Proxy Test

Status: **complete**

## Provenance

- Dataset: SEN12MS-CR
- Real sensors: Sentinel-1 SAR + Sentinel-2 multispectral
- Mirror used for one streamed sample: Hugging Face `Hermanni/sen12mscr`
- Original source declared by the mirror: mediaTUM 1554803
- Season: `spring`
- Scene: `1`
- Patch: `p100`
- S1 shape: `[2, 256, 256]`
- S2 shape: `[13, 256, 256]`

## SatQuery result

- Job ID: `5c34325588204f95bb94cc41f7811bd2`
- Task: `FUSION_ANALYSIS`
- Decision: `INSUFFICIENT_EVIDENCE`
- Trust score: `0.0`
- Validation: `see REAL_PROXY_JOB.json`

## Scientific boundary

This is a **real-sensor Sentinel-1/Sentinel-2 cross-modal proxy run**. The mirror provides paired sensor arrays but does not expose the original product CRS/geotransform in each row. The generated local TIFFs intentionally do **not** invent a CRS. Any SatQuery `READY_WITH_LIMITATIONS` / metadata warning is expected and should be preserved in the evidence.

This test does **not** prove Cartosat-2S/RISAT performance and must not be presented as such.
