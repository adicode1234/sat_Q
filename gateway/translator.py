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

    try:
        res = httpx.get(
            'https://translate.googleapis.com/translate_a/single',
            params={'client': 'gtx', 'sl': 'auto', 'tl': target, 'dt': 't', 'q': clean},
            timeout=10.0
        )
        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated = ''.join([part[0] for part in data[0] if part and len(part) > 0 and part[0]])
                if translated:
                    _CACHE[cache_key] = translated
                    return translated
    except Exception as e:
        print(f"[Translator Exception] {e}", flush=True)

    return text

def translate_texts(texts: list[str], target: str) -> list[str]:
    if not texts or target not in ('hi', 'bn'):
        return texts
    return [translate_single(t, target) for t in texts]
