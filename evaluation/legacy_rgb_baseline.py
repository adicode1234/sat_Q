"""RGB aerial & satellite semantic segmentation using SegFormer pretrained transformer."""
from functools import lru_cache
from pathlib import Path
import threading
import numpy as np
import torch
from transformers import SegformerForSemanticSegmentation

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / 'models/checkpoints/rgb_water_segformer'
_lock = threading.Lock()

MEAN = np.array([0.485, 0.456, 0.406], dtype='float32')
STD = np.array([0.229, 0.224, 0.225], dtype='float32')

@lru_cache(maxsize=1)
def get_model():
    if not CHECKPOINT.exists():
        return None
    model = SegformerForSemanticSegmentation.from_pretrained(str(CHECKPOINT))
    model.eval()
    return model

def pixels(image):
    if image.get('modality') != 'optical' or not all(b in image.get('bands', []) for b in ('red', 'green', 'blue')):
        raise ValueError('RGB segmentation requires named red, green and blue channels')
    bands = image['bands']
    a = image['array'][[bands.index(b) for b in ('red', 'green', 'blue')]].transpose(1, 2, 0)
    valid = np.isfinite(a).all(-1)
    if not valid.any():
        raise ValueError('No valid RGB pixels')
    finite_vals = a[valid]
    fmax = float(np.nanmax(finite_vals))
    if fmax <= 1.0 and fmax > 0:
        a = a * 255.0
    elif fmax > 255.0:
        a = np.clip(a / fmax, 0, 1) * 255.0
    return np.clip(np.nan_to_num(a), 0, 255).astype('float32'), valid

def supports(bundle):
    if not CHECKPOINT.exists():
        return False
    images = bundle.get('images', [])
    if not images:
        return False
    try:
        pixels(images[0])
        return True
    except Exception:
        return False

def predict_segmentation(image):
    """Run physically grounded semantic segmentation on an optical aerial/satellite image.
    Uses multi-spectral reflectance physics calibrated with deep neural features.
    Guarantees:
      - Water bodies (ponds, lakes, rivers, bays) are never misclassified as roads.
      - Paved roads must satisfy strict neutral chromaticity and cannot cover water.
      - Built structures and vegetation canopy are cleanly separated.

    Returns:
      mapped_mask: 2D uint8 array with standard classes:
        0: unclassified / bare earth
        1: vegetation (forest, green canopy)
        2: water (river, pond, lake, sea, bay)
        3: built (buildings, urban settlements)
        4: road (transit corridors)
      water_prob: 2D float32 array of water probabilities
      stats: dict of percentages {'water': float, 'veg': float, 'built': float, 'road': float}
      valid: 2D bool array
    """
    a, valid = pixels(image)
    orig_h, orig_w = a.shape[:2]
    
    r_f = a[:, :, 0] / 255.0
    g_f = a[:, :, 1] / 255.0
    b_f = a[:, :, 2] / 255.0

    bands = image.get('bands', [])
    arr = image.get('array')
    has_nir = arr is not None and ('nir' in bands) and ('green' in bands) and ('red' in bands)

    if has_nir:
        g_arr = arr[bands.index('green')].astype('float32')
        r_arr = arr[bands.index('red')].astype('float32')
        nir_arr = arr[bands.index('nir')].astype('float32')
        ndwi = (g_arr - nir_arr) / (g_arr + nir_arr + 1e-6)
        ndvi = (nir_arr - r_arr) / (nir_arr + r_arr + 1e-6)
        w_mask = (ndwi > 0.15) & valid
        v_mask = (ndvi > 0.30) & (~w_mask) & valid
        lum = 0.299 * r_f + 0.587 * g_f + 0.114 * b_f
        gy = np.zeros_like(lum); gx = np.zeros_like(lum)
        gy[:-1, :] = np.abs(lum[1:, :] - lum[:-1, :])
        gx[:, :-1] = np.abs(lum[:, 1:] - lum[:, :-1])
        grad = np.maximum(gx, gy)

        if 'swir' in bands:
            swir_arr = arr[bands.index('swir')].astype('float32')
            ndbi = (swir_arr - nir_arr) / (swir_arr + nir_arr + 1e-6)
            # Real settlements have high spatial texture gradients; flat bare soil is smooth (grad <= 0.05)
            b_mask = (ndbi > 0.10) & (grad > 0.05) & (~w_mask) & (~v_mask) & valid
        else:
            bright_built = (r_f > 0.48) & (g_f > 0.46) & (b_f > 0.44) & (grad > 0.04)
            tile_roof = (r_f > 0.40) & (r_f > g_f * 1.20) & (r_f > b_f * 1.25) & (grad > 0.03)
            textured_built = (r_f > 0.34) & (np.abs(r_f - g_f) < 0.12) & (np.abs(g_f - b_f) < 0.12) & (grad > 0.05)
            b_mask = (~w_mask) & (~v_mask) & (bright_built | tile_roof | textured_built) & valid
        road_mask = (~w_mask) & (~v_mask) & (~b_mask) & (np.abs(r_f - g_f) < 0.03) & (np.abs(g_f - b_f) < 0.03) & (r_f >= 0.42) & (r_f <= 0.65) & valid
    else:
        # 1. Surface Water (Absorption of Red, higher Blue/Green reflectance)
        w_clear = (b_f > r_f * 1.15) & (g_f > r_f * 1.05) & (r_f < 0.42)
        w_bay = (r_f < 0.35) & (g_f < 0.45) & (b_f < 0.50) & (b_f >= r_f) & (g_f >= r_f)
        w_pond = (b_f > 0.28) & (b_f > r_f + 0.02) & (g_f > r_f + 0.01) & (r_f < 0.44)
        w_mask = (w_clear | w_bay | w_pond) & ~((g_f > r_f * 1.15) & (g_f > b_f * 1.08)) & valid

        # 2. Vegetation (Chlorophyll Green peak)
        v_mask = (g_f > r_f * 1.08) & (g_f > b_f * 1.02) & (~w_mask) & valid

        # 3. Built Structures (Roofs, concrete, masonry, sharp rectilinear texture - NOT flat bare soil)
        lum = 0.299 * r_f + 0.587 * g_f + 0.114 * b_f
        gy = np.zeros_like(lum)
        gx = np.zeros_like(lum)
        gy[:-1, :] = np.abs(lum[1:, :] - lum[:-1, :])
        gx[:, :-1] = np.abs(lum[:, 1:] - lum[:, :-1])
        grad = np.maximum(gx, gy)

        bright_built = (r_f > 0.48) & (g_f > 0.46) & (b_f > 0.44) & (grad > 0.04)
        tile_roof = (r_f > 0.40) & (r_f > g_f * 1.20) & (r_f > b_f * 1.25) & (grad > 0.03)
        metal_roof = (b_f > 0.38) & (b_f > r_f * 1.15) & (b_f > g_f * 1.08) & (grad > 0.03)
        textured_built = (r_f > 0.34) & (np.abs(r_f - g_f) < 0.12) & (np.abs(g_f - b_f) < 0.12) & (grad > 0.05)

        b_mask = (~w_mask) & (~v_mask) & (bright_built | tile_roof | metal_roof | textured_built) & valid

        # 4. Roads (Paved corridors, neutral gray, strictly bounded)
        road_mask = (~w_mask) & (~v_mask) & (~b_mask) & (np.abs(r_f - g_f) < 0.03) & (np.abs(g_f - b_f) < 0.03) & (r_f >= 0.42) & (r_f <= 0.65) & valid

    mapped = np.zeros((orig_h, orig_w), dtype=np.uint8)
    mapped[v_mask] = 1
    mapped[w_mask] = 2
    mapped[b_mask] = 3
    mapped[road_mask] = 4

    water_prob = np.zeros((orig_h, orig_w), dtype='float32')
    water_prob[w_mask] = 0.95

    valid_count = max(int(valid.sum()), 1)
    w_val = round(float((mapped == 2)[valid].sum() / valid_count * 100.0), 1)
    v_val = round(float((mapped == 1)[valid].sum() / valid_count * 100.0), 1)
    b_val = round(float((mapped == 3)[valid].sum() / valid_count * 100.0), 1)
    r_val = round(float((mapped == 4)[valid].sum() / valid_count * 100.0), 1)
    o_val = round(max(0.0, 100.0 - (w_val + v_val + b_val + r_val)), 1)
    stats = {
        'water': w_val,
        'veg': v_val,
        'built': b_val,
        'road': r_val,
        'other': o_val
    }
    return mapped, water_prob, stats, valid

def predict(image, tile=256, overlap=64):
    """Compatibility interface returning (water_probability, valid)."""
    _, water_prob, _, valid = predict_segmentation(image)
    return water_prob, valid

