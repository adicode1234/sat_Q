"""Authoritative physical calculation of NDVI and NDWI.
Strictly requires actual physical spectral bands (NIR, Red, Green).
Never fabricates or estimates indices for RGB-only imagery.
"""
from typing import Dict, Any, List, Optional
import numpy as np


def compute_spectral_indices(image: Dict[str, Any]) -> Dict[str, Any]:
    bands = [b.lower() for b in image.get("bands", [])]
    arr = image.get("array")

    has_nir = any(b in bands for b in ("nir", "b8", "b8a"))
    has_red = any(b in bands for b in ("red", "b4"))
    has_green = any(b in bands for b in ("green", "b3"))

    # If NIR is missing (standard RGB image like web/phone uploads):
    if not has_nir or arr is None or arr.size == 0:
        return {
            "status": "not available",
            "reason": "Spectral indices not available for RGB image",
            "missing_bands": ["nir"],
            "available_bands": bands,
            "indices": {
                "ndvi": {
                    "status": "not available",
                    "value": None,
                    "reason": "Near-Infrared (NIR) band required for physical NDVI calculation"
                },
                "ndwi": {
                    "status": "not available",
                    "value": None,
                    "reason": "Near-Infrared (NIR) band required for physical NDWI calculation"
                }
            },
            "provenance": {
                "method": "spectral_indices_validator_v1",
                "bands_evaluated": bands
            }
        }

    # Multispectral imagery with true NIR band present:
    nir_band = next(b for b in ("nir", "b8", "b8a") if b in bands)
    nir_idx = bands.index(nir_band)
    nir = arr[nir_idx].astype(np.float32)

    indices_result = {}

    # NDVI: (NIR - Red) / (NIR + Red)
    if has_red:
        red_band = next(b for b in ("red", "b4") if b in bands)
        red_idx = bands.index(red_band)
        red = arr[red_idx].astype(np.float32)
        denom_ndvi = nir + red
        denom_ndvi = np.where(np.abs(denom_ndvi) < 1e-7, 1e-7, denom_ndvi)
        ndvi_arr = (nir - red) / denom_ndvi
        valid_ndvi = ndvi_arr[np.isfinite(ndvi_arr)]

        indices_result["ndvi"] = {
            "status": "available",
            "mean": round(float(valid_ndvi.mean()), 4) if valid_ndvi.size else None,
            "min": round(float(valid_ndvi.min()), 4) if valid_ndvi.size else None,
            "max": round(float(valid_ndvi.max()), 4) if valid_ndvi.size else None,
            "vegetation_fraction": round(float((valid_ndvi > 0.3).mean()), 4) if valid_ndvi.size else 0.0,
            "formula": "(NIR - Red) / (NIR + Red)",
            "bands_used": [nir_band, red_band]
        }
    else:
        indices_result["ndvi"] = {
            "status": "not available",
            "value": None,
            "reason": "Red band required for NDVI"
        }

    # NDWI: (Green - NIR) / (Green + NIR)
    if has_green:
        green_band = next(b for b in ("green", "b3") if b in bands)
        green_idx = bands.index(green_band)
        green = arr[green_idx].astype(np.float32)
        denom_ndwi = green + nir
        denom_ndwi = np.where(np.abs(denom_ndwi) < 1e-7, 1e-7, denom_ndwi)
        ndwi_arr = (green - nir) / denom_ndwi
        valid_ndwi = ndwi_arr[np.isfinite(ndwi_arr)]

        indices_result["ndwi"] = {
            "status": "available",
            "mean": round(float(valid_ndwi.mean()), 4) if valid_ndwi.size else None,
            "min": round(float(valid_ndwi.min()), 4) if valid_ndwi.size else None,
            "max": round(float(valid_ndwi.max()), 4) if valid_ndwi.size else None,
            "water_fraction": round(float((valid_ndwi > 0.15).mean()), 4) if valid_ndwi.size else 0.0,
            "formula": "(Green - NIR) / (Green + NIR)",
            "bands_used": [green_band, nir_band]
        }
    else:
        indices_result["ndwi"] = {
            "status": "not available",
            "value": None,
            "reason": "Green band required for NDWI"
        }

    return {
        "status": "available",
        "available_bands": bands,
        "indices": indices_result,
        "provenance": {
            "method": "calibrated_physical_indices_v1",
            "bands_evaluated": bands
        }
    }
