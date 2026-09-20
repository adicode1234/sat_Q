# SatQuery AI — Completion Pack

This pack closes every **actionable** item from the 12 Sep 2026 audit without pretending that unavailable data has been validated.

## What this pack closes

- Promotes the newest 72-sample benchmark artifact to `evaluation/results.json` so `/api/benchmarks` and the dashboard use the latest verified run.
- Re-runs all four built-in demos on the final rebuilt Docker services and writes final E2E evidence.
- Runs a fresh grounding paraphrase/contrast test against the live `/api/jobs` pipeline.
- Creates the four missing evidence documents:
  - `docs/REAL_WORLD_PROXY_TEST.md`
  - `docs/LIMITATIONS.md`
  - `docs/ADAPTATION_JUSTIFICATION.md`
  - `evaluation/README.md`
- Generates a VQA error-analysis artifact from the latest evaluation.
- Optionally streams one **real Sentinel-1/Sentinel-2 SEN12MS-CR pair** from a public Hugging Face mirror and submits it to SatQuery's cross-modal pipeline. The mirror derives from the real SEN12MS-CR Sentinel-1/Sentinel-2 dataset. The conversion may not preserve the original CRS/geotransform, so the report explicitly labels this as **real-sensor proxy validation with metadata limitations**, not Cartosat/RISAT validation.
- Optionally runs browser smoke QA with Playwright and stores desktop/mobile screenshots plus console-error evidence.

## What no script can truthfully mark complete without external data

1. **Full official VRSBench/RSVQA/CDVQA leaderboard reproduction** — the local manifest currently contains only 4 VRSBench, 64 RSVQA and 4 CDVQA examples.
2. **Real Cartosat-2S/RISAT validation** — requires genuine organizer/authorized data.

Those two items are documented as external validation boundaries rather than falsely marked PASS.

## Run

From the SatQuery project root:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\satquery_completion_pack\complete_remaining_tasks.ps1" -Root $PWD
```

For the real Sentinel proxy test too:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\satquery_completion_pack\complete_remaining_tasks.ps1" -Root $PWD -RunRealProxy
```

For browser smoke QA too:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\satquery_completion_pack\complete_remaining_tasks.ps1" -Root $PWD -RunBrowserQA
```

For **everything actionable in one run**:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\satquery_completion_pack\complete_remaining_tasks.ps1" -Root $PWD -RunRealProxy -RunBrowserQA
```

Evidence is written under `docs/evidence/`.
