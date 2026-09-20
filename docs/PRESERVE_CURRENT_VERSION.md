# Restore this exact SatQuery version

This snapshot includes the source, the currently served compiled frontend, the
Hindi/Bengali translations, backend translation route, browser speech controls,
walkthrough video, and local model checkpoints. Large assets use Git LFS.

## Get the complete copy

```sh
git lfs install
git clone https://github.com/adicode1234/Query_sat.git
cd Query_sat
git lfs pull
python3 scripts/verify_release.py
```

A GitHub ZIP may contain LFS pointers instead of the media/models. Prefer the
clone commands above. The verifier rejects missing or changed assets.

## Run without changing the UI

Use Python 3.12, create a virtual environment, and install requirements.txt.
For local neural models also install requirements-ml.txt. The reference machine's
full Python package versions are recorded in local-python-environment.txt;
platform-specific packages may differ on other operating systems.

Copy .env.example to .env and configure the same providers and Supabase project
using your own secret values. Do not commit .env or API keys. Launch with:

```sh
bash start_satquery.sh
```

The checked-in frontend/dist is the current UI. There is no need to run npm
install or rebuild it to restore this snapshot. Docker now serves that reviewed
build by default. To intentionally rebuild, pass --build-arg REBUILD_FRONTEND=1.
To include local neural dependencies in Docker, pass --build-arg WITH_ML=1 and
use a host with sufficient memory/storage for the checked-in models.

## Hosting and feature checks

Run the full FastAPI application, not frontend/dist alone or GitHub Pages.
The UI uses /api/translate, authentication, analysis, previews, and history from
the backend. Ensure your deployment downloads Git LFS objects before building.
Keep the existing provider, model, and Supabase environment configuration on the
hosting platform; these secret settings are not part of GitHub.

After deployment:

1. Sign in, switch to Hindi and Bengali, and check both labels and a report.
2. Click Listen/Stop; test the browser's installed voices for each language.
3. Allow microphone access and test voice input in a compatible browser over
   HTTPS (localhost is suitable for local use).
4. Play the walkthrough and run an analysis with your configured provider.
5. Open a saved analysis from History.

Translation needs access to the existing Google translation endpoint. Speech
recognition and synthesis depend on the browser, microphone permissions, and
available language voices. Provider limits, hosting memory, and browser behavior
can differ even when files are identical. This snapshot does not change those
implementations or guarantee external service availability.

User uploads, saved reports, sessions, .env, node_modules, and the virtual
environment remain local. Back up reports/ and data/uploads/ privately if you
want existing private history on a new machine. Configure persistent storage on
hosting to retain future uploads and reports across redeployments.
