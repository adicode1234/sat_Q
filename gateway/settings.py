"""Deployment limits shared by inspection, execution and the public configuration API."""
import os
from gateway.errors import InputError


def positive(name, default):
    value = int(os.environ.get(name, default))
    if value < 1:
        raise RuntimeError(f'{name} must be positive')
    return value


MAX_UPLOADS = positive('SATQUERY_MAX_UPLOADS', 20)
MAX_UPLOAD_MB = positive('SATQUERY_MAX_UPLOAD_MB', 128)
MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_QUERY_CHARS = positive('SATQUERY_MAX_QUERY_CHARS', 8000)
MAX_MULTIDATE = min(positive('SATQUERY_MAX_MULTIDATE', 20), MAX_UPLOADS)
# Includes all observations, channels and normalization scratch space estimates.
MAX_DECODED_MB = positive('SATQUERY_MAX_DECODED_MB', 1024)
MIN_OVERLAP = .2


def enabled(operation):
    return os.environ.get('SATQUERY_AUTO_' + operation, '1') == '1'


def query_text(query):
    query = query.strip()
    if not query or len(query) > MAX_QUERY_CHARS:
        raise InputError(f'Query must contain 1–{MAX_QUERY_CHARS} characters; received {len(query)}.',
                         'QUERY_LENGTH_EXCEEDED', 'Shorten the query; it has not been truncated.')
    return query


def check_count(scenario, count):
    if not 1 <= count <= MAX_UPLOADS:
        raise InputError(f'Maximum {MAX_UPLOADS} uploads; received {count}.', 'UPLOAD_COUNT_EXCEEDED')
    if scenario == 'MULTI_DATE' and not 3 <= count <= MAX_MULTIDATE:
        raise InputError(f'Multi-date requires 3–{MAX_MULTIDATE} observations; received {count}.', 'MULTIDATE_COUNT_EXCEEDED')
    expected = {'SINGLE': 1, 'BITEMPORAL_PAIR': 2, 'CROSS_MODAL_PAIR': 2, 'MULTI_DATE': count}
    if scenario not in expected or expected[scenario] != count:
        raise InputError('Scenario and image count do not match', 'SCENARIO_COUNT_MISMATCH')


def check_size(size):
    if size > MAX_BYTES:
        raise InputError(f'Maximum {MAX_UPLOAD_MB} MiB; received {size / 1024**2:.2f} MiB.',
                         'FILE_TOO_LARGE', 'Crop, tile, compress, or use a smaller region.')
