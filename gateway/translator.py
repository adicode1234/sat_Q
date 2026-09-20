import httpx

_CACHE = {}

def translate_single(text: str, target: str) -> str:
    if not text or not isinstance(text, str) or not text.strip() or target not in ('hi', 'bn'):
        return text
    clean = text.strip()
    cache_key = (clean, target)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    # Preserve multi-paragraph formatting by translating paragraphs individually
    if '\n\n' in clean:
        paragraphs = clean.split('\n\n')
        translated_paras = [translate_single(p.strip(), target) for p in paragraphs if p.strip()]
        result = '\n\n'.join(translated_paras)
        _CACHE[cache_key] = result
        return result

    # Strategy 1: Google Translate gtx with realistic Browser User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        res = httpx.get(
            'https://translate.googleapis.com/translate_a/single',
            params={'client': 'gtx', 'sl': 'auto', 'tl': target, 'dt': 't', 'q': clean},
            headers=headers,
            timeout=8.0
        )
        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated = ''.join([part[0] for part in data[0] if part and len(part) > 0 and part[0]])
                if translated and translated.strip() and translated.strip() != clean:
                    _CACHE[cache_key] = translated
                    return translated
    except Exception as e:
        print(f"[Translator Google Exception] {e}", flush=True)

    # Strategy 2: MyMemory Translation API (free, reliable fallback for cloud datacenters)
    try:
        res = httpx.get(
            'https://api.mymemory.translated.net/get',
            params={'q': clean[:500], 'langpair': f'en|{target}'},
            headers=headers,
            timeout=8.0
        )
        if res.status_code == 200:
            data = res.json()
            translated = data.get('responseData', {}).get('translatedText')
            if translated and translated.strip() and translated.strip() != clean and 'MYMEMORY WARNING' not in translated:
                _CACHE[cache_key] = translated
                return translated
    except Exception as e:
        print(f"[Translator MyMemory Exception] {e}", flush=True)

    # Strategy 3: Fast LLM translation if OpenRouter is configured in environment
    try:
        import os
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        if openrouter_key:
            target_name = 'Hindi' if target == 'hi' else 'Bengali'
            res = httpx.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {openrouter_key}', 'Content-Type': 'application/json'},
                json={
                    'model': 'inclusionai/ling-3.0-flash-vl:free',
                    'messages': [{'role': 'user', 'content': f'Translate this satellite analysis text to natural {target_name}. Return ONLY the direct translation:\n{clean}'}],
                    'temperature': 0.1
                },
                timeout=12.0
            )
            if res.status_code == 200:
                translated = res.json()['choices'][0]['message']['content'].strip()
                if translated and translated != clean:
                    _CACHE[cache_key] = translated
                    return translated
    except Exception as e:
        print(f"[Translator LLM Exception] {e}", flush=True)

    return text

def translate_texts(texts: list[str], target: str) -> list[str]:
    if not texts or target not in ('hi', 'bn'):
        return texts
    return [translate_single(t, target) for t in texts]
