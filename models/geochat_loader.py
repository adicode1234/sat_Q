"""GeoChat-7B remote-sensing large vision-language model loader and inference wrapper.

Detects local archive (satquery-geochat-permanent-backup.zip, geochat-7b.zip) or
extracted checkpoint in models/checkpoints/geochat.
"""
from pathlib import Path
import os
import zipfile
import logging

ROOT = Path(__file__).resolve().parents[1]
GEOCHAT_DIR = ROOT / 'models/checkpoints/geochat'

logger = logging.getLogger('satquery.geochat')

def find_geochat_archive():
    """Scan workspace and downloads for any GeoChat archive."""
    candidates = [
        ROOT / 'satquery-geochat-permanent-backup.zip',
        ROOT / 'geochat-7b.zip',
        ROOT / 'models/checkpoints/satquery-geochat-permanent-backup.zip',
        ROOT / 'models/checkpoints/geochat.zip',
        Path.home() / 'Downloads/satquery-geochat-permanent-backup.zip',
        Path.home() / 'Downloads/geochat-7b.zip',
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 1000000:
            return p
    return None

def ensure_geochat_extracted():
    """Extract GeoChat archive if found and not already extracted."""
    if (GEOCHAT_DIR / 'config.json').exists() or (GEOCHAT_DIR / 'model.safetensors').exists() or (GEOCHAT_DIR / 'adapter_config.json').exists():
        return True
    
    archive = find_geochat_archive()
    if archive is None:
        return False
    
    GEOCHAT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Extracting GeoChat archive from {archive} to {GEOCHAT_DIR}...")
    try:
        with zipfile.ZipFile(archive, 'r') as zf:
            zf.extractall(GEOCHAT_DIR)
        logger.info("GeoChat extraction complete.")
        return True
    except Exception as e:
        logger.error(f"Failed to extract GeoChat archive: {e}")
        return False

def is_geochat_available():
    """Check if GeoChat model weights are ready for inference."""
    if ensure_geochat_extracted():
        return True
    return False

def get_geochat_status():
    """Return human-readable status of GeoChat model integration."""
    if is_geochat_available():
        return {
            'status': 'available',
            'path': str(GEOCHAT_DIR),
            'message': 'GeoChat remote sensing model weights detected and available.'
        }
    archive = find_geochat_archive()
    if archive:
        return {
            'status': 'archive_detected',
            'path': str(archive),
            'message': f'Archive found at {archive.name}; ready to unpack on first use.'
        }
    return {
        'status': 'standby',
        'message': 'Waiting for satquery-geochat-permanent-backup.zip in project folder or Downloads.'
    }
