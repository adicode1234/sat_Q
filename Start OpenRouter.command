#!/bin/zsh
cd -- "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  print 'Python environment missing: create .venv and install requirements.txt first.'
  exit 1
fi
export SATQUERY_VISION_PROVIDER=openrouter
print 'SatQuery OpenRouter setup: http://127.0.0.1:8766/vision-setup'
print 'Paste your OpenRouter key in the API Key box. Keep this terminal open.'
exec .venv/bin/python -m uvicorn gateway.app:app --host 127.0.0.1 --port 8766
