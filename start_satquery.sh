#!/bin/bash
# ==============================================================================
# SatQuery AI — Server Launch Script
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Load environment variables from .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

export SATQUERY_PIPELINE="${SATQUERY_PIPELINE:-legacy}"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

echo "============================================="
echo "🛰️  SatQuery AI - Satellite Intelligence Gateway"
echo "   Pipeline Mode : $SATQUERY_PIPELINE"
echo "   Host & Port   : http://$HOST:$PORT"
echo "============================================="

# Detect Python executable
if [ -f ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

exec "$PYTHON" -m uvicorn gateway.app:app --host "$HOST" --port "$PORT"
