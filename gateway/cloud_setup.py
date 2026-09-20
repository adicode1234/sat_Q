"""Local-only opt-in credential configuration, no credential persistence or echoes."""
import os, secrets
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from models import cloud_vision

router = APIRouter()

def local_request(request: Request):
    if request.url.hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise HTTPException(403, 'Cloud settings are available only on localhost.')
    origin = request.headers.get('origin')
    if origin and origin != str(request.base_url).rstrip('/'):
        raise HTTPException(403, 'Cross-origin settings requests are blocked.')

@router.get('/api/vision/settings')
def get_settings(request: Request):
    local_request(request)
    return cloud_vision.status()

@router.post('/api/vision/settings')
async def set_settings(request: Request):
    local_request(request)
    if not secrets.compare_digest(request.headers.get('x-satquery-csrf', ''), cloud_vision._nonce):
        raise HTTPException(403, 'Reload Cloud vision setup and try again.')
    if int(request.headers.get('content-length', '0')) > 4096:
        raise HTTPException(413, 'Settings body too large.')
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(400, 'Expected JSON settings.')
    if not isinstance(body, dict):
        raise HTTPException(400, 'Expected settings object.')
    if body.get('enabled') is False:
        cloud_vision.configure(None, False)
        return cloud_vision.status()

    provider = body.get('provider', 'gemini')
    if provider not in cloud_vision.PROVIDERS:
        raise HTTPException(400, 'Choose OpenRouter, OpenRouter, Google Gemini, OpenAI, or Local Ollama.')

    if not isinstance(body.get('model', ''), str):
        raise HTTPException(400, 'Model must be a text model identifier.')
    custom_model = (body.get('model') or '').strip()
    if len(custom_model) > 200 or any(c.isspace() for c in custom_model):
        raise HTTPException(400, 'Enter a valid model identifier without spaces.')
    if provider == 'ollama':
        model = custom_model or os.environ.get('OLLAMA_MODEL', '').strip()
        if not model:
            raise HTTPException(400, 'Enter an Ollama model name (e.g. llama3.2-vision, llava, or minicpm-v).')
        if not cloud_vision.is_ollama_running(timeout=2.0):
            raise HTTPException(502, 'Ollama server start karo: connection to http://localhost:11434 refused. Terminal me "ollama serve" chalao.')
        cloud_vision.configure(None, True, provider, model=model)
        return cloud_vision.status()

    key = body.get('api_key')
    if not isinstance(key, str) or not 20 <= len(key.strip()) <= 512 or '\n' in key or '\r' in key:
        raise HTTPException(400, 'Enter a valid API key.')
    key = key.strip()

    # Format-based provider/key matching (no network call needed — key is verified at inference time)
    if key.startswith('AIza') and provider != 'gemini':
        raise HTTPException(400, 'This looks like a Google API key. Select "Google Gemini" as provider.')
    if key.startswith('sk-or-') and provider != 'openrouter':
        raise HTTPException(400, 'This looks like an OpenRouter key. Select "OpenRouter" as provider.')
    if key.startswith('sk-') and not key.startswith('sk-or-') and provider not in ('openai', 'novita'):
        raise HTTPException(400, 'This looks like an OpenAI key. Select "OpenAI" as provider.')

    if provider == 'gemini':
        model = custom_model or os.environ.get('GEMINI_MODEL', '')
    else:
        model = custom_model or cloud_vision.PROVIDERS[provider][1]

    # For Gemini: do a lightweight live model-list check (doesn't send any images)
    if provider == 'gemini':
        endpoint, headers = cloud_vision.connection(provider, key, model)
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(endpoint, headers=headers)
            if response.status_code != 200:
                raise HTTPException(400, f'Gemini key validation failed (HTTP {response.status_code}). Check your API key.')
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, 'Could not reach Google API. Check your connection.')


    output_format = 'json_schema'
    if provider == 'openrouter':
        # Check live catalog (best-effort — :free variants may not be individually listed)
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                catalog = await client.get('https://openrouter.ai/api/v1/models')
            # Auth errors = bad key; re-raise as user-facing error
            if catalog.status_code in (401, 403):
                raise HTTPException(400, f'OpenRouter key validation failed (HTTP {catalog.status_code}). Check your API key.')
            if catalog.status_code != 200:
                # Non-auth server errors: allow with fallback
                print(f"[OpenRouter] Catalog returned HTTP {catalog.status_code} — proceeding with prompt_json fallback", flush=True)
                output_format = 'prompt_json'
            else:
                entries = catalog.json().get('data', [])
                if isinstance(entries, dict):
                    entries = list(entries.values()) if entries else []
                # Try exact match first, then base model (strip :free/:nitro suffix)
                base_model = model.split(':')[0]
                selected = (next((m for m in entries if isinstance(m, dict) and m.get('id') == model), None) or
                            next((m for m in entries if isinstance(m, dict) and m.get('id') == base_model), None))
                if selected is not None:
                    modalities = selected.get('architecture', {}).get('input_modalities', [])
                    # Only block if we are CERTAIN it has no image support
                    if modalities and 'image' not in modalities and 'file' not in modalities:
                        raise HTTPException(400, f'Model "{model}" does not appear to support image inputs on OpenRouter. Choose a vision-capable model (e.g. inclusional/ling-3.0-flash-vl:free).')
                    supported = selected.get('supported_parameters') or []
                    # Free tier community endpoints often fail response_format; use prompt_json
                    if ':free' in model:
                        output_format = 'prompt_json'
                    else:
                        output_format = ('json_schema' if 'structured_outputs' in supported else
                                         'json_object' if 'response_format' in supported else 'prompt_json')
                else:
                    # Model not found in catalog — new/:free variant; allow with prompt_json fallback
                    print(f"[OpenRouter] Model '{model}' not in catalog — proceeding with prompt_json fallback", flush=True)
                    output_format = 'prompt_json'
        except HTTPException:
            raise
        except Exception as exc:
            # Network error (offline / timeout) — allow with fallback, key verified at inference
            print(f"[OpenRouter] Catalog check failed ({exc}) — proceeding with prompt_json fallback", flush=True)
            output_format = 'prompt_json'

    cloud_vision.configure(key, True, provider, model=model, output_format=output_format)
    return cloud_vision.status()

@router.get('/vision-setup', response_class=HTMLResponse)
def setup_page(request: Request):
    local_request(request)
    return HTMLResponse('''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cloud vision · SatQuery</title><style>body{background:#071321;color:#e4eef8;font:16px system-ui;max-width:650px;margin:8vh auto;padding:24px}input,button,select{box-sizing:border-box;width:100%;padding:14px;margin:10px 0;border-radius:8px;border:1px solid #345;background:#10263a;color:white}button{background:#007eab;cursor:pointer;font-weight:bold}a{color:#62d5ff}p{line-height:1.6}#status{color:#8bdddf;font-weight:600}.hint{font-size:13px;color:#94a3b8;margin-top:-4px}</style></head><body><a href="/">← Back to SatQuery</a><h1>Cloud & Vision AI Setup</h1><p>Analyze uploaded images with OpenRouter, Google Gemini, OpenAI, or Local Ollama. Images and questions are sent to the selected provider when you run an analysis. OpenRouter forwards them to the chosen model provider; usage is billed to your account. Connecting only validates your key and model. OpenRouter connection selects API analysis instead of the unavailable local specialists.</p><p>The API key stays in server memory only until restart. Local Ollama runs completely offline on your machine without requiring an API key.</p><p id="status">Loading…</p><form id="form"><label for="provider">Provider</label><select id="provider"><option value="openrouter">OpenRouter</option><option value="gemini">Google Gemini</option><option value="openai">OpenAI</option><option value="ollama">Local Ollama (no key)</option></select><label for="model">Model Name</label><input id="model" type="text" placeholder="OpenRouter: google/gemini-2.5-flash" autocomplete="off"><div class="hint" id="modelHint">OpenRouter default: google/gemini-2.5-flash; model must accept images; SatQuery validates the returned report</div><div id="keyGroup"><label for="key">API Key</label><input id="key" type="password" autocomplete="off" placeholder="Paste API key here" required></div><button id="connect" type="submit">Connect and enable vision AI</button></form><button id="disconnect" type="button" style="background:#471515;border-color:#7f1d1d">Disable vision AI</button><p><a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">Get Google Gemini API key</a> · <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">Get OpenAI API key</a> · <a href="https://ollama.com" target="_blank" rel="noopener noreferrer">Download Ollama</a></p><script>
let token='';const status=document.querySelector('#status');
function updateProviderUI(){const p=document.querySelector('#provider').value;const isOllama=p==='ollama';document.querySelector('#keyGroup').style.display=isOllama?'none':'block';document.querySelector('#key').required=!isOllama;document.querySelector('#modelHint').textContent=isOllama?'e.g. llama3.2-vision, llava (must support vision)':'OpenRouter default: google/gemini-2.5-flash; model must accept images; SatQuery validates the returned report';}
document.querySelector('#provider').onchange=()=>{document.querySelector('#model').value='';updateProviderUI();};
async function refresh(){const r=await fetch('/api/vision/settings');const d=await r.json();token=d.csrf_token;if(d.enabled){document.querySelector('#provider').value=d.provider_id;document.querySelector('#model').value=d.model||'';}updateProviderUI();status.textContent=d.enabled?'Connected · Provider: '+d.provider+' · Model: '+(d.model||'(auto)'):'Not connected · paste your key below';}
async function save(body){const r=await fetch('/api/vision/settings',{method:'POST',headers:body?{'Content-Type':'application/json','X-SatQuery-CSRF':token}:{'X-SatQuery-CSRF':token},body:body?JSON.stringify(body):JSON.stringify({enabled:false})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));await refresh();}
document.querySelector('#form').onsubmit=async e=>{e.preventDefault();const p=document.querySelector('#provider').value;const input=document.querySelector('#key');const key=p==='ollama'?'':input.value;input.value='';const button=document.querySelector('#connect');button.disabled=true;status.textContent='Validating model & connection with provider…';try{await save({api_key:key,enabled:true,provider:p,model:document.querySelector('#model').value});status.textContent='Connected! Return to SatQuery and upload your images. OpenRouter uses API mode automatically.';}catch(e){status.textContent='Error: '+e.message;}finally{button.disabled=false;}};
document.querySelector('#disconnect').onclick=async()=>{try{await save(null);}catch(e){status.textContent=e.message;}};refresh().catch(()=>status.textContent='Could not load settings.');</script></body></html>''', headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})
