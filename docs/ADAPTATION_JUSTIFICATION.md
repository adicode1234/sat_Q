# Remote-Sensing Adaptation Justification

SatQuery uses a VRSBench-based LoRA/ViLT adaptation path rather than claiming a full BigEarthNet reproduction. The project requirement permits remote-sensing adaptation using BigEarthNet **or other open-source training data**. VRSBench is directly aligned with remote-sensing vision-language tasks and therefore provides task-relevant supervision for visual question answering and language-conditioned analysis. This choice is a pragmatic task-aligned adaptation, not a claim that VRSBench and BigEarthNet are equivalent datasets.

Current limitation: adaptation is small-scale and does not establish production-level generalization to Cartosat-2S/RISAT imagery. Real-domain proxy evidence is tracked separately in `REAL_WORLD_PROXY_TEST.md`.
