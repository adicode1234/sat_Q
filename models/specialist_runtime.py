"""Explicit runtime boundary for installed specialist implementations.

SATQUERY_<NAME>_RUNTIME is a trusted server-configured module exposing run(bundle, call).
No generic model substitution, archive extraction, downloads, or weight mutation occurs here.
"""
import importlib
import os


def runtime_status(name):
    configured = bool(os.environ.get(f'SATQUERY_{name.upper()}_RUNTIME'))
    return {'name': name, 'status': 'configured_unverified' if configured else 'unavailable',
            'model_loaded': None, 'runtime_verified': False}


def run(bundle, call):
    name = call['specialist']
    module = os.environ.get(f'SATQUERY_{name.upper()}_RUNTIME')
    if not module:
        raise RuntimeError(f'{name} runtime unavailable. Configure SATQUERY_{name.upper()}_RUNTIME with an installed specialist implementation.')
    raw = importlib.import_module(module).run(bundle, call)
    if not isinstance(raw, dict) or raw.get('specialist') != name:
        raise ValueError('Specialist runtime must return matching specialist provenance.')
    return raw
