# 🛰️ SatQuery AI — Satellite & Earth Observation Intelligence Platform

> **Production-Ready Multi-Modal Satellite Intelligence Workspace**  
> AI-powered remote-sensing query analysis, physical spectral verification (NDVI / NDWI / NDBI), optical + SAR multi-source fusion, live WebSocket execution trace, and executive PDF reporting.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-7.1-646cff.svg)](https://vitejs.dev)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ed.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📑 Table of Contents
1. [System Overview & Architecture](#-system-overview--architecture)
2. [Folder Structure](#-folder-structure)
3. [Environment Configuration (`.env`)](#-environment-configuration-env)
4. [Local Deployment (Quickstart)](#-local-deployment-quickstart)
5. [Docker Deployment](#-docker-deployment)
6. [Cloud Platform Deployments](#-cloud-platform-deployments)
   - [A. Render.com (Recommended Free/Easy)](#a-rendercom-recommended-easy)
   - [B. Railway.app](#b-railwayapp)
   - [C. Hugging Face Spaces](#c-hugging-face-spaces)
   - [D. Fly.io](#d-flyio)
   - [E. Linux VPS / AWS EC2 / DigitalOcean (Nginx + Systemd + SSL)](#e-linux-vps--aws-ec2--digitalocean-droplet)
7. [Automated Deployment Verification](#-automated-deployment-verification)
8. [Production Security & Optimization](#-production-security--optimization)

---

## 🔭 System Overview & Architecture

SatQuery AI provides an end-to-end mission control cockpit for satellite analysts and decision-makers:
- **Multi-Modal Vision Language Models (VLM):** Integrated OpenRouter / Gemini cloud vision specialists for natural language queries against high-resolution optical and SAR scenes.
- **Physical Verification Engine:** Independent, deterministic band-math algorithms computing NDVI (vegetation), NDWI (water extent), and NDBI (built-up areas) to prevent AI hallucination.
- **Cross-Modal Fusion:** Reconciles optical and SAR radar data, flagging physical discrepancies and adjusting confidence trust scores.
- **Executive PDF & Audio Reports:** Instant client-side PDF export and multi-lingual voice interpretation (Hindi, English, Bengali).
- **Responsive Mission UI:** Adapts from desktop multi-monitor cockpits to smartphone viewports.

### 6-Layer Engine Architecture
```
┌────────────────────────────────────────────────────────────────────────┐
│                        User Interface & Cockpit                        │
│       React 18 + CesiumJS 3D Globe + Vite + Mobile Touch View          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP & WebSockets
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 1: Gateway & Validation (`gateway/validation.py`, `app.py`)      │
│ Checks format, dimensions, CRS, bounds, memory limits, and auth token.  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 2: Controller & Registry (`controller/pipeline.py`)              │
│ Tool registry dispatch, scenario qualification, dependency order.      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 3: Model Execution (`models/`)                                   │
│ OpenRouter VLM, ViLT VQA, Grounding DINO, Siamese Change Detection.    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 4: Physical Verification (`verification/engine.py`)              │
│ Deterministic raster calculations: NDVI, NDWI, NDBI, and SAR dB checks.│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 5: Consensus & Fusion (`fusion_engine/consensus.py`)             │
│ Optical-SAR consensus, evidence union, confidence calibration.        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Layer 6: Reports & Review (`gateway/reporting.py`, `review_queue.py`)  │
│ Mission reports, candidate review dashboard, JSON audit export.        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Folder Structure

The repository is organized for clean deployment separation between gateway services, frontend assets, machine learning models, and configuration:

```text
satquery-ai/
├── Dockerfile                  # Production multi-stage Docker build (Node 22 + Python 3.12)
├── docker-compose.yml          # Multi-container orchestration (Gateway + Specialists)
├── docker-compose.ml.yml       # Extended GPU/ML compose configuration
├── requirements.txt            # Core production Python dependencies
├── requirements-ml.txt         # Optional heavy ML libraries (PyTorch, Transformers)
├── start_satquery.sh           # Executable production startup script (Linux/macOS)
├── start.ps1                   # Executable PowerShell startup script (Windows)
├── .env.example                # Template for environment variables
├── .dockerignore               # Optimized Docker build context exclusions
├── .gitignore                  # Git repository exclusion rules
│
├── configs/                    # Pipeline configuration
│   └── tool_registry.yaml      # Specialist tools, routing scores, and parameter limits
│
├── controller/                 # Pipeline orchestration
│   └── pipeline.py             # Event emitter, dependency resolution, execution engine
│
├── data/                       # Test datasets, demo GeoTIFFs, and upload staging
│   ├── demo/                   # Bundled synthetic satellite scenes (Optical, SAR, Pair)
│   └── uploads/                # Temporary local file uploads (gitignored)
│
├── docs/                       # Technical documentation & audit reports
│   ├── OPENROUTER_SETUP.md     # Vision provider configuration guide
│   ├── REAL_IMAGERY_UPGRADE.md # Sensor calibration and band mapping guide
│   └── LIMITATIONS.md          # Known sensor and model constraints
│
├── frontend/                   # Modern React 18 frontend (Vite + TypeScript + CSS)
│   ├── components/             # React components (CesiumGlobe, HUD, Profile, Modals)
│   ├── routes/                 # Main cockpit views, styling, and internationalization
│   ├── services/               # API, WebSocket, and Supabase client bindings
│   ├── package.json            # Frontend package dependencies
│   ├── vite.config.ts          # Vite bundler configuration
│   └── dist/                   # Production compiled assets (served by FastAPI)
│
├── fusion_engine/              # Multi-sensor reconciliation
│   └── consensus.py            # Optical + SAR agreement logic and trust penalty
│
├── gateway/                    # FastAPI web server and routing
│   ├── app.py                  # Main HTTP / WebSocket application entrypoint
│   ├── auth.py                 # Supabase token validation and auth middleware
│   ├── cloud_setup.py          # Vision AI provider runtime configurator
│   ├── reporting.py            # HTML / JSON report rendering
│   └── review_queue.py         # Human-in-the-loop analyst review database
│
├── models/                     # Vision & neural specialist implementations
│   ├── cloud_vision.py         # OpenRouter, Gemini, and Ollama integration
│   ├── vqa_caption/            # Single optical VQA and captioning
│   ├── grounding/              # Spatial object candidate localization
│   └── change_vqa/             # Bitemporal change detection
│
├── verification/               # Independent physical ground-truth verifier
│   └── engine.py               # Deterministic NDVI, NDWI, NDBI and SAR threshold checks
│
├── scripts/                    # Maintenance and operational utilities
│   └── health_check.py         # Automated deployment health verification script
│
└── tests/                      # Automated unit and integration test suite
```

---

## 🔑 Environment Configuration (`.env`)

Before deploying, create a `.env` file in the project root by copying the template:

```bash
cp .env.example .env
```

### Configuration Variables Reference

| Variable Name | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `SATQUERY_PIPELINE` | **Yes** | `legacy` | Core pipeline mode. Use `legacy` for in-process verified neural & physical models. |
| `SATQUERY_CLOUD_VISION` | Optional | `1` | Set `1` to enable multi-modal reasoning; `0` for offline physical heuristics only. |
| `SATQUERY_VISION_PROVIDER` | Optional | `openrouter` | Provider name: `openrouter`, `gemini`, `ollama`, or `novita`. |
| `OPENROUTER_API_KEY` | Optional | - | API Key from [OpenRouter](https://openrouter.ai/keys) for Vision LLMs. |
| `OPENROUTER_MODEL` | Optional | `inclusionai/ling-3.0-flash-vl:free` | Vision model ID (e.g. `inclusionai/ling-3.0-flash-vl:free` or `google/gemini-2.0-flash-exp:free`). |
| `GEMINI_API_KEY` | Optional | - | API Key from [Google AI Studio](https://aistudio.google.com/) if using Gemini. |
| `SUPABASE_URL` | Optional | - | Supabase project URL for authentication & user accounts. |
| `SUPABASE_PUBLISHABLE_KEY` | Optional | - | Supabase public anon key for frontend session validation. |
| `HOST` | Optional | `0.0.0.0` | Host interface for server binding (`0.0.0.0` for Docker/cloud). |
| `PORT` | Optional | `8000` | Port for server listening (auto-detected on Render/Railway). |
| `SATQUERY_MAX_UPLOAD_MB` | Optional | `128` | Maximum single satellite image upload size in megabytes. |

---

## 🚀 Local Deployment (Quickstart)

### Prerequisites
- **Python:** 3.12 or newer
- **Node.js:** 20 or newer (only needed if building frontend from source)

### 1. Clone & Setup Python Environment
```bash
git clone https://github.com/your-org/satquery-ai.git
cd satquery-ai

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install Python backend dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and enter your OpenRouter or Supabase keys
```

### 3. Build the React Frontend
```bash
cd frontend
npm ci
npm run build
cd ..
```

### 4. Launch the Server
```bash
# On Linux / macOS:
./start_satquery.sh

# Or directly with Uvicorn:
uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```
Open your browser at **`http://127.0.0.1:8000`**.

---

## 🐳 Docker Deployment

The repository includes an optimized **multi-stage Dockerfile**:
- **Stage 1 (Node 22):** Builds and optimizes the React Vite frontend.
- **Stage 2 (Python 3.12-slim):** Installs Python requirements, mounts the compiled UI, and runs Uvicorn. The container image remains compact (~300MB).

### Single Container (Recommended for Quick Cloud Hosting)

```bash
# 1. Build the Docker container image
docker build -t satquery-ai:latest .

# 2. Run the container with your .env configuration
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name satquery-instance \
  satquery-ai:latest
```
Access the application at `http://localhost:8000`.

### Multi-Container Docker Compose

To deploy with separate microservices for each specialist model:
```bash
docker compose up -d --build
```
To view real-time logs:
```bash
docker compose logs -f gateway
```

---

## ☁️ Cloud Platform Deployments

### A. Render.com (Recommended — Easy & Free Tier Available)

Render automatically detects the multi-stage `Dockerfile` and deploys both backend and frontend as a unified service with free automated SSL.

1. Push your repository to **GitHub** or **GitLab**.
2. Sign in to [Render.com](https://render.com) and click **New +** → **Web Service**.
3. Select your `satquery-ai` repository.
4. Set the following options:
   - **Name:** `satquery-ai`
   - **Region:** Any close to you (e.g., Oregon, Frankfurt, Singapore)
   - **Runtime:** **Docker** (Render uses the root `Dockerfile`)
   - **Instance Type:** Free or Starter (>= 1 GB RAM recommended for raster processing)
5. Under **Environment Variables**, add:
   - `SATQUERY_PIPELINE` = `legacy`
   - `SATQUERY_CLOUD_VISION` = `1`
   - `SATQUERY_VISION_PROVIDER` = `openrouter`
   - `OPENROUTER_API_KEY` = `your_openrouter_api_key`
   - `OPENROUTER_MODEL` = `inclusionai/ling-3.0-flash-vl:free`
   - `SUPABASE_URL` = `your_supabase_url`
   - `SUPABASE_PUBLISHABLE_KEY` = `your_supabase_key`
6. Click **Create Web Service**.
7. In ~3 minutes, your platform will be live at `https://satquery-ai.onrender.com`!

---

### B. Railway.app

Railway provides fast, zero-configuration Docker deployments with automatic `$PORT` injection.

1. Go to [Railway.app](https://railway.app) and create a **New Project**.
2. Select **Deploy from GitHub repo** and choose `satquery-ai`.
3. Go to the project **Variables** tab and set:
   ```env
   SATQUERY_PIPELINE=legacy
   SATQUERY_CLOUD_VISION=1
   SATQUERY_VISION_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-xxxx
   OPENROUTER_MODEL=inclusionai/ling-3.0-flash-vl:free
   ```
4. Railway will build the `Dockerfile` automatically and provide a public HTTPS domain under **Settings → Networking → Generate Domain**.

---

### C. Hugging Face Spaces

You can host SatQuery AI as a free public demo space on Hugging Face:

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Choose **Space SDK: Docker** → **Blank**.
3. Clone your Space repo locally and push the `satquery-ai` code into it:
   ```bash
   git remote add hf https://huggingface.co/spaces/your-username/satquery-ai
   git push hf main
   ```
4. In Space **Settings → Variables and Secrets**, add your `OPENROUTER_API_KEY`, `SUPABASE_URL`, etc.
5. Hugging Face will build the Docker container and expose port `7860` (our Dockerfile automatically respects `$PORT`).

---

### D. Fly.io

1. Install the Fly CLI: `brew install flyctl` or `curl -L https://fly.io/install.sh | sh`
2. Run in the project directory:
   ```bash
   fly launch --no-deploy
   ```
3. Set your deployment secrets:
   ```bash
   fly secrets set \
     SATQUERY_PIPELINE=legacy \
     SATQUERY_CLOUD_VISION=1 \
     SATQUERY_VISION_PROVIDER=openrouter \
     OPENROUTER_API_KEY=your_key_here
   ```
4. Deploy:
   ```bash
   fly deploy
   ```

---

### E. Linux VPS / AWS EC2 / DigitalOcean Droplet

For dedicated production environments on Ubuntu / Debian:

#### 1. System Setup
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv git nginx certbot python3-certbot-nginx

# Clone repository
git clone https://github.com/your-org/satquery-ai.git /var/www/satquery-ai
cd /var/www/satquery-ai

# Setup environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Compile frontend
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
cd frontend && npm ci && npm run build && cd ..

# Setup .env
cp .env.example .env
nano .env
```

#### 2. Configure Systemd Service
Create `/etc/systemd/system/satquery.service`:
```ini
[Unit]
Description=SatQuery AI Application Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/satquery-ai
EnvironmentFile=/var/www/satquery-ai/.env
ExecStart=/var/www/satquery-ai/.venv/bin/uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo chown -R www-data:www-data /var/www/satquery-ai
sudo systemctl daemon-reload
sudo systemctl enable --now satquery
sudo systemctl status satquery
```

#### 3. Nginx Reverse Proxy with WebSocket Support
Create `/etc/nginx/sites-available/satquery`:
```nginx
server {
    server_name yourdomain.com;

    client_max_body_size 128M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and install SSL:
```bash
sudo ln -s /etc/nginx/sites-available/satquery /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 🧪 Automated Deployment Verification

After launching your server or container, run the automated health check script:

```bash
python3 scripts/health_check.py
```

### Expected Output:
```text
🛰️  Verifying SatQuery AI Service Health at: http://127.0.0.1:8000
------------------------------------------------------------
  ✅ [PASS] Root Landing Page         -> HTTP 200
  ✅ [PASS] Auth Session Endpoint     -> HTTP 200
  ✅ [PASS] Workspace Auth Guard      -> HTTP 401 (Protected as expected)
  ✅ [PASS] Static Logo Asset         -> HTTP 200
  ✅ [PASS] Favicon Vector            -> HTTP 200
------------------------------------------------------------
🎉 All deployment health checks passed successfully!
```

---

## 🔒 Production Security & Optimization

1. **Keep Secrets Safe:**
   - Never commit `.env` into git. The `.gitignore` is preconfigured to prevent secret leakage.
   - On cloud providers (Render, Railway, Fly.io), use the platform's native **Environment Secrets** dashboard.

2. **CORS & Origin Hardening:**
   - In `gateway/app.py`, WebSocket and session origins are checked to prevent cross-site hijacking. When using a custom domain, ensure requests originate from your domain.

3. **Memory & Upload Governance:**
   - GeoTIFF rasters can be large when uncompressed. Keep `SATQUERY_MAX_DECODED_MB=1024` to prevent Out-Of-Memory (OOM) events on low-spec cloud instances.
   - The gateway enforces `asyncio.Semaphore(1)` concurrency for heavy raster decoding jobs to guarantee stability.

4. **Temporary Uploads Cleanup:**
   - Uploaded GeoTIFFs and temporal analysis jobs are stored in `data/uploads/`.
   - Setup a cron job to purge files older than 24 hours in high-traffic deployments:
     ```bash
     0 2 * * * find /var/www/satquery-ai/data/uploads -type f -mtime +1 -delete
     ```

---

## 📄 License & Attribution

- **Project:** SatQuery AI — Vision-Language Satellite Intelligence System
- **Authors & Team:** SatQuery Research Team
- **Notice:** Satellite sensor names (e.g. Sentinel-1 SAR, Sentinel-2 Optical) and ISRO references in test fixtures are standard remote-sensing benchmarks used for scientific evaluation and verification.

