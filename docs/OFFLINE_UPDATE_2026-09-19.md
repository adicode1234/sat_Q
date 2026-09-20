# Local-only update — 19 September 2026

Cloud credential routes, cloud setup UI and cloud model dispatch have been removed. The previously configured key was cleared from memory. Server starts with HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1.

The analysis UI no longer announces completion on a timer: it waits for the actual server result, displays server progress and polls status if its WebSocket disconnects. This also clears the previous result before starting another image.

## Training and evaluation

Each SAR, optical and joint water model received 1,200 additional optimization steps; RGB received three 600-step learning-rate trials. Existing fixed chip splits were preserved; weights/calibration were selected using validation IoU and Brier score, never test scores. These are repeat evaluations on previously inspected data, not a new independent benchmark. Sensor and screenshot transfer remain unvalidated.

| Model | Validation IoU before | Validation IoU after | New weights deployed |
|---|---:|---:|---|
| sar | 0.5543 | 0.5543 | False |
| optical | 0.8324 | 0.8330 | True |
| joint | 0.8364 | 0.8379 | True |
| RGB water | 0.4096 | 0.4148 | True |

Pretrained SegFormer and Grounding DINO are retained: the local data has no suitable six-class pixel labels or object boxes for meaningful retraining. Prior VQA and change-model refinements showed no improvement and are not deployed; their labelled data comprises only six images and two image pairs respectively. Synthetic-only fusion/tiny training does not establish real-image accuracy. Arbitrary-image captioning is not supported by these specialist checkpoints.

Validation: 98 pipeline/evidence/normalization/regression tests plus 2 offline-mode tests passed; production frontend build passed; Grounding DINO and fusion checkpoint inference smoke tests passed. Model disagreement continues to withhold unreliable water overlays instead of asserting a river or invented area.
