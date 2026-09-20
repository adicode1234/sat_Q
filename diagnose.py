"""Diagnostic tool for SatQuery AI Cloud Vision (Google Gemini) integration.
Audits environment variables, Google API connectivity, model availability,
schema generation, and pipeline routing WITHOUT printing or leaking credentials.
"""
import os, sys, json, base64, io
from pathlib import Path
import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def run_diagnostics():
    print("=" * 70)
    print("          SATQUERY CLOUD VISION (GOOGLE GEMINI) DIAGNOSTIC")
    print("=" * 70)

    first_failure = None
    all_passed = True

    # 1. Environment Variables Check
    key_env = os.environ.get("GEMINI_API_KEY")
    model_env = os.environ.get("GEMINI_MODEL")
    cloud_vision_env = os.environ.get("SATQUERY_CLOUD_VISION")

    key_status = "SET (Present)" if bool(key_env and key_env.strip()) else "NOT SET (Missing)"
    model_status = f"SET ('{model_env}')" if bool(model_env and model_env.strip()) else "NOT SET (Missing)"
    cloud_status = f"SET ('{cloud_vision_env}')" if cloud_vision_env is not None else "NOT SET (Missing)"

    print(f"\n[1] Environment Variables:")
    print(f"    • GEMINI_API_KEY          : {key_status}")
    print(f"    • GEMINI_MODEL            : {model_status}")
    print(f"    • SATQUERY_CLOUD_VISION   : {cloud_status}")

    if not key_env or not key_env.strip():
        print("    --> FAIL: GEMINI_API_KEY is not set in environment.")
        all_passed = False
        first_failure = first_failure or "GEMINI_API_KEY environment variable is not set. Run: export GEMINI_API_KEY='your-key'"
    elif cloud_vision_env != "1":
        print("    --> FAIL: SATQUERY_CLOUD_VISION is not '1'. Cloud vision will not auto-enable on startup.")
        all_passed = False
        first_failure = first_failure or "SATQUERY_CLOUD_VISION must be set to '1'. Run: export SATQUERY_CLOUD_VISION=1"
    else:
        print("    --> PASS: Key and Cloud Vision enable flag are set.")

    # 2. ListModels API Connectivity
    models_found = []
    if key_env and key_env.strip():
        print(f"\n[2] Google ListModels API Check:")
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": key_env.strip()}
        try:
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("models", [])
                # Filter models supporting generateContent
                gen_models = [m for m in raw_models if "generateContent" in m.get("supportedGenerationMethods", [])]
                models_found = [m.get("name", "").replace("models/", "") for m in gen_models]
                print(f"    --> PASS: Connected successfully. Found {len(models_found)} models supporting generateContent (total {len(raw_models)}).")
            else:
                print(f"    --> FAIL: ListModels returned HTTP {resp.status_code}: {resp.text}")
                all_passed = False
                first_failure = first_failure or f"ListModels failed with HTTP {resp.status_code}. Verify GEMINI_API_KEY validity."
        except Exception as exc:
            print(f"    --> FAIL: Connection error: {type(exc).__name__}: {exc}")
            all_passed = False
            first_failure = first_failure or f"Cannot connect to generativelanguage.googleapis.com ({exc})"
    else:
        print(f"\n[2] Google ListModels API Check: SKIPPED (No API key)")

    # 3. Model Availability Check
    print(f"\n[3] Model Availability Check:")
    if models_found:
        target_model = model_env.strip() if (model_env and model_env.strip()) else "None"
        if target_model in models_found:
            print(f"    --> PASS: Configured model '{target_model}' is active and supports generateContent.")
        else:
            print(f"    --> FAIL: Model '{target_model}' was NOT found in account's generateContent models.")
            print(f"    First 10 available models in your account:")
            for m in models_found[:10]:
                print(f"      - {m}")
            all_passed = False
            first_failure = first_failure or f"Model '{target_model}' not found in account. Choose from available models above."
    else:
        print("    --> FAIL: No models could be retrieved to verify GEMINI_MODEL.")

    # 4. Dummy Image generateContent Live Test
    print(f"\n[4] Live generateContent Test (100x100 dummy image):")
    if key_env and key_env.strip() and model_env and model_env.strip():
        # Create solid color dummy image
        buf = io.BytesIO()
        Image.new('RGB', (100, 100), color=(70, 130, 180)).save(buf, format='PNG')
        b64_img = base64.b64encode(buf.getvalue()).decode('ascii')

        from models.cloud_vision import SCHEMA, INSTRUCTIONS
        test_payload = {
            'systemInstruction': {'parts': [{'text': INSTRUCTIONS}]},
            'contents': [{
                'role': 'user',
                'parts': [
                    {'text': 'Identify any visible land cover features.'},
                    {'inlineData': {'mimeType': 'image/png', 'data': b64_img}}
                ]
            }],
            'generationConfig': {
                'responseMimeType': 'application/json',
                'responseJsonSchema': SCHEMA,
                'maxOutputTokens': 8192
            }
        }
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_env.strip()}:generateContent"
        try:
            resp = httpx.post(endpoint, headers={"x-goog-api-key": key_env.strip()}, json=test_payload, timeout=30)
            print(f"    Google HTTP Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    raw_text = "".join([p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []) if not p.get("thought")]).strip()
                    try:
                        parsed = json.loads(raw_text)
                        has_fields = all(k in parsed for k in ("image_type", "visible_features", "uncertainties", "answer"))
                        if has_fields:
                            print(f"    --> PASS: Model returned valid JSON matching all schema fields.")
                            print(f"        Detected Image Type: {parsed.get('image_type')}")
                            print(f"        Answer Preview     : {parsed.get('answer')[:80]}...")
                        else:
                            print(f"    --> FAIL: Response JSON missing required schema fields. Found: {list(parsed.keys())}")
                            all_passed = False
                            first_failure = first_failure or "Gemini JSON response missing schema fields."
                    except Exception as parse_err:
                        print(f"    --> FAIL: JSON parse error: {parse_err}. Raw text:\n{raw_text}")
                        all_passed = False
                        first_failure = first_failure or f"Failed to parse model output as JSON: {parse_err}"
                else:
                    print(f"    --> FAIL: No candidates returned. Full response:\n{resp.text}")
                    all_passed = False
                    first_failure = first_failure or "Google API returned empty candidates."
            else:
                err_clean = resp.text.replace(key_env.strip(), "[REDACTED_KEY]")
                print(f"    --> FAIL: Google API error (HTTP {resp.status_code}):\n{err_clean}")
                all_passed = False
                first_failure = first_failure or f"generateContent returned HTTP {resp.status_code}: {resp.text}"
        except Exception as exc:
            print(f"    --> FAIL: Request exception: {type(exc).__name__}: {exc}")
            all_passed = False
            first_failure = first_failure or f"generateContent exception: {exc}"
    else:
        print("    --> SKIPPED: Missing API key or GEMINI_MODEL.")

    # 5. cloud_enabled() Runtime State Check
    print(f"\n[5] Runtime cloud_enabled() Check:")
    from models.cloud_vision import enabled as cloud_enabled, configuration as cloud_cfg
    c_key, c_model, c_prov = cloud_cfg()
    is_active = cloud_enabled()
    if is_active:
        print(f"    --> PASS: cloud_enabled() is True (Provider: {c_prov}, Model: {c_model})")
    else:
        reason = []
        if not c_key:
            if not key_env:
                reason.append("No API key in memory or GEMINI_API_KEY environment")
            elif cloud_vision_env != "1":
                reason.append("GEMINI_API_KEY is present in env, BUT SATQUERY_CLOUD_VISION is not '1'")
        if not c_model:
            reason.append("No GEMINI_MODEL configured")
        why = "; ".join(reason) or "Cloud vision inactive"
        print(f"    --> FAIL: cloud_enabled() is False ({why})")
        all_passed = False
        first_failure = first_failure or f"cloud_enabled() is False: {why}"

    # 6. Pipeline Connection Check
    print(f"\n[6] Pipeline Route Integration Check:")
    pipeline_code = (ROOT / "controller/pipeline.py").read_text()
    has_cloud_check = "from models.cloud_vision import enabled as cloud_enabled" in pipeline_code
    has_cloud_dispatch = "return run_cloud(bundle, query, analysis_id, trace, event, started)" in pipeline_code
    cloud_pipeline_exists = (ROOT / "controller/cloud_pipeline.py").exists()

    if has_cloud_check and has_cloud_dispatch and cloud_pipeline_exists:
        print("    --> PASS: controller/pipeline.py delegates to controller/cloud_pipeline.py when enabled.")
    else:
        print(f"    --> FAIL: Pipeline route incomplete (check={has_cloud_check}, dispatch={has_cloud_dispatch}, file={cloud_pipeline_exists})")
        all_passed = False
        first_failure = first_failure or "Pipeline cloud routing is incomplete."

    # Final Summary
    print("\n" + "=" * 70)
    print("                         SUMMARY")
    print("=" * 70)
    if all_passed:
        print("STATUS: READY")
        print("All cloud vision checks passed! Google Gemini will execute accurately.")
    else:
        print(f"STATUS: NOT READY")
        print(f"FIRST BLOCKER TO FIX: {first_failure}")
    print("=" * 70)

if __name__ == "__main__":
    run_diagnostics()
