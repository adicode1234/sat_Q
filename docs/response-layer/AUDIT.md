# Pre-implementation audit — 19 September 2026

Root: /Users/adityarajput/Downloads/satquery-ai. This copy has no .git directory.

React/Vite frontend/src.jsx mounts frontend/routes/index.tsx (classic workspace also retained). Multipart /api/jobs and /api/analyze enter gateway/app.py, execute() invokes controller.pipeline.run_pipeline. WebSocket /api/trace and GET /api/jobs expose the same result; gateway writes JSON and HTML reports and previews.

Validation in gateway/validation.py decodes images, checks resource limits, formats, bands, modalities and dates. gateway/normalization.py checks grids, reprojects compatible rasters, and rejects unestablished optical/SAR overlap. Temporal upload-slot ordering without dates is explicitly user-declared. Grid compatibility is not independent proof of sensor registration.

RegistryClassifier chooses eligible tools by scenario and keyword score. Model calls go through the bounded executor or configured HTTP services and gateway/contracts.py. Physical verification and fusion follow inference, but controller/scene_analyzer.py can replace the final answer. Model failures are collected in the existing decision gate.

GeoChat: PLACEHOLDER. models/geochat_loader.py discovers/extracts archives; no inference function and no caller in the active pipeline. Checkpoint not present.
TEOChat: MISSING. No integration or checkpoint found. Actual temporal route uses controller.temporal_analysis plus legacy Siamese change-VQA and appearance masks.
EarthMind: MISSING. No integration or checkpoint found. Actual cross-modal route uses legacy cross-attention fusion or water experts.
These are code audit classifications, not runtime validations of the legacy networks.

Cloud vision: when enabled, controller/pipeline.py returns controller/cloud_pipeline.py before registry selection. Gemini/OpenAI/Ollama independently interpret previews. Cloud inventory adds unsupported absence/safety statements. Existing cloud setup/API remains available but must not override the requested specialists.

Existing contracts provide claims, limitations, numerical uncalibrated scores, execution traces, verification, overlays and provenance. Missing: named specialist routing, insufficient-input intent gates, uniform modality-specific evidence, calibrated-confidence availability, and report source preservation. Frontend PDF generation includes fabricated default percentages and findings. No lint script is configured; TypeScript and Vite build are available.

Plan: extend the existing registry/pipeline with strict named-specialist selection and configured Python runtime adapters; preserve legacy behavior only via an explicit environment setting. Reuse image validation, executor, API/jobs/trace and exports. Add one validated analysis report contract and a matching frontend component. Never download, extract, alter or train weights. Test orchestration with marked mocks, failures without mocks, and existing regression suites separately.
