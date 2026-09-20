# Named specialist runtime configuration

The default pipeline requires GeoChat, TEOChat and EarthMind. None of their inference implementations or checkpoints is installed in this workspace. The supplied runtime boundary does not implement those architectures. Configuring an environment variable alone does not make a model available or verified.

Install each specialist's compatible runtime and weights separately, then provide an importable Python module for each installed implementation. Each module must expose `run(bundle, call)`. Select the modules using server environment variables `SATQUERY_GEOCHAT_RUNTIME`, `SATQUERY_TEOCHAT_RUNTIME`, and `SATQUERY_EARTHMIND_RUNTIME`. Values are Python import paths, not checkpoint paths, model IDs or URLs. Do not point these at generic cloud models. An HTTP deployment would need a model-specific adapter; the new runtime boundary currently supports Python modules only.

`bundle` is the existing validated image bundle. `bundle['images']` contains decoded band-first NumPy arrays, band names, modality (`optical` or `SAR`), image IDs, shape, dates, preprocessing history and metadata. Temporal images are ordered before/after. Cross-modal arrays retain modality labels; adapters must use those labels rather than assuming optical comes first. Normalized working paths also remain available internally. Do not send imagery externally unless deliberately configured and disclosed.

`call` contains the original `query`, selected `task`, `specialist`, `image_ids`, empty public `params`, and `response_policy`. The installed adapter must run the selected real model on the actual supplied arrays/images and enforce the policy in its model prompt. It must not substitute illustrative answers, ignore one sensor, infer model identity from the requested name, or report a mock as inference.

Return a dictionary validated by `gateway.contracts.RuntimeResponse`:

- `specialist`: exactly GeoChat, TEOChat or EarthMind, matching the executed model.
- `model`: actual model/checkpoint identifier used.
- `answer`: nonempty actual specialist answer; report formatting preserves this string exactly.
- `observations`: optional list of evidence items.
- `evidence`: optional object with lists `general`, `before`, `after`, `optical`, `sar`, `agreement`, `disagreement`, `added`, `removed`, `reduced`, `expanded`, `unchanged`.
- `uncertainty`: optional list of source limitations.

Every evidence item has `text`, nonempty `image_ids`, and `kind`: observed, inferred, uncertain or unsupported. Omitting `kind` yields uncertain. Keep an absent evidence category empty. Do not use another language model to manufacture sections that the specialist did not provide. Evidence source IDs, modalities and temporal roles are checked. Unknown fields and malformed values cause controlled failure. Free-text scientific correctness is not machine-certified by this schema.

Numerical confidence and runtime-supplied geometry are deliberately not accepted by this text contract. Confidence remains null with an explanation. For GeoChat grounding requests, the existing local Grounding DINO detector can run after a successful GeoChat call and supply genuine candidate boxes; `SATQUERY_USE_DINO=0` disables it. Boxes and detector scores are uncalibrated and are not object counts. Missing detector dependencies result in an explicit warning. The text answer is never rewritten from boxes.

There is no TEOChat-specific change map integration yet. Before/after evidence can be reported as text; missing visual evidence stays empty. The preserved legacy change-mask path remains available only in legacy mode.

## Run

From the project root:

```sh
cd /Users/adityarajput/Downloads/satquery-ai
.venv/bin/python -m uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Without configured specialist runtimes, valid analyses return `MODEL_FAILURE` / `MODEL_UNAVAILABLE` reports. HTTP job completion describes transport/report generation, not successful model inference. Inspect `decision` and `execution_summary.processing_status`.

For the existing research models and optional cloud-vision mode, explicitly opt in:

```sh
SATQUERY_PIPELINE=legacy .venv/bin/python -m uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

Legacy mode retains its existing model names, research limitations and cloud setup behavior. It is not GeoChat, TEOChat or EarthMind and is not covered by the new report-integrity guarantees. Cloud settings never override named-specialist mode.

Frontend development/build:

```sh
cd /Users/adityarajput/Downloads/satquery-ai/frontend
npm run dev
npm exec tsc -- --noEmit
npm run build
```

Verification:

```sh
cd /Users/adityarajput/Downloads/satquery-ai
SATQUERY_USE_DINO=0 SATQUERY_PIPELINE=legacy .venv/bin/python -m pytest tests -q
.venv/bin/python -m pytest tests/test_specialist_reports.py -q
.venv/bin/python -m compileall -q controller gateway models/specialist_runtime.py
```

The combined command explicitly exercises the old tests in legacy mode; new tests override that setting and verify the default named-specialist path. These are orchestration tests, not real named-model inference tests. No lint script is configured.
