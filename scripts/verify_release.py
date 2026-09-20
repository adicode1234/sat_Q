"""Verify source, compiled UI, and LFS assets against this reviewed snapshot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()

def main():
    manifest = json.loads((ROOT / 'release-manifest.json').read_text())
    failures = []
    for name, expected in manifest['files'].items():
        path = ROOT / name
        if not path.is_file() or digest(path) != expected:
            failures.append(name)
    if failures:
        print('Missing or changed files (run git lfs pull for large assets):')
        print('\n'.join(failures))
        return 1
    print(f"PASS: {len(manifest['files'])} files match the reviewed snapshot.")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
