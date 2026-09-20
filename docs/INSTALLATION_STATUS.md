# Windows installation handoff

Docker/WSL installation is authorized but incomplete as of 2026-09-11.

- Official Docker Desktop installer downloaded successfully (604,875,184 bytes). Its Authenticode signature verified as Docker Inc.
- Windows administrator process launch failed with `0xc0000142`.
- The per-user Docker installer could not create its AppData log folder from the restricted command environment, even after the requested folder permissions were granted. Docker is not installed.
- No Windows restart or license acceptance was performed.

Run `install-prerequisites.ps1` yourself in PowerShell as Administrator. It uses the downloaded installer when available, verifies its signature, installs WSL/Docker, and leaves any restart and Docker agreement acceptance to you. After Docker starts, stop the native server using port 8000 and run `verify-docker.ps1` to verify the seven-service deployment. An actual passing container run will create `tests/docker_results.json`; this file is intentionally absent until then.

The native app at http://127.0.0.1:8000 is available independently of Docker while its server is running. The code, trained small models, evaluation evidence, and source package are delivered. Container runtime verification is the outstanding deployment check.

Official references: [Docker installation](https://docs.docker.com/desktop/setup/install/windows-install/) and [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install).
