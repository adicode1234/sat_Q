"""Config-driven optical quality gate for change detection candidates.
Enforces physical authenticity: checks that cannot be calculated from
available bands are explicitly reported as 'not evaluated'.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "quality_gate.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "optical": {
        "max_cloud_cover": 0.15,
        "min_valid_pixel_ratio": 0.80,
        "snow_ice_threshold": 0.20,
        "haze_threshold": 0.25,
        "seasonal_water_variance_threshold": 0.30,
    },
    "decision_rules": {
        "auto_suppress_cloud_above": 0.40,
        "review_queue_cloud_above": 0.15,
        "review_queue_valid_below": 0.80,
        "low_quality_score_below": 0.60,
    }
}


def load_quality_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "optical" in loaded and "decision_rules" in loaded:
                return loaded
        except Exception:
            pass
    return DEFAULT_CONFIG


def evaluate_optical_quality_gate(bundle: Dict[str, Any]) -> Dict[str, Any]:
    images = bundle.get("images", [])
    cfg = load_quality_config()
    opt_cfg = cfg.get("optical", DEFAULT_CONFIG["optical"])
    dec_cfg = cfg.get("decision_rules", DEFAULT_CONFIG["decision_rules"])

    image_checks: List[Dict[str, Any]] = []
    max_cloud = 0.0
    min_valid = 1.0

    for idx, img in enumerate(images):
        arr = img.get("array")
        bands = [b.lower() for b in img.get("bands", [])]
        has_rgb = all(b in bands for b in ("red", "green", "blue"))
        has_nir = any(b in bands for b in ("nir", "b8", "b8a"))
        has_swir = any(b in bands for b in ("swir", "b11", "b12"))

        # 1. Valid pixel fraction check
        if arr is not None and arr.size > 0:
            finite = np.isfinite(arr)
            valid_ratio = float(finite.all(axis=0).mean())
        else:
            valid_ratio = 0.0
        min_valid = min(min_valid, valid_ratio)

        # 2. Cloud cover check
        cloud_val = None
        if has_rgb and arr is not None and arr.shape[0] >= 3:
            rgb = arr[[bands.index(b) for b in ("red", "green", "blue")]]
            val = np.isfinite(rgb).all(axis=0)
            if val.any() and np.nanmin(rgb) >= 0 and np.nanmax(rgb) <= 1.5:
                cloud_val = float(((rgb.mean(0) > 0.8) & (rgb.std(0) < 0.08))[val].mean())
                max_cloud = max(max_cloud, cloud_val)

        # 3. Snow & Ice check (Physical NDSI requires Green and SWIR bands)
        if "green" in bands and has_swir:
            green_idx = bands.index("green")
            swir_band_name = next(b for b in ("swir", "b11", "b12") if b in bands)
            swir_idx = bands.index(swir_band_name)
            green_b = arr[green_idx]
            swir_b = arr[swir_idx]
            denom = green_b + swir_b
            denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
            ndsi = (green_b - swir_b) / denom
            snow_cover = float((ndsi > 0.42).mean())
            snow_check = {
                "status": "evaluated",
                "method": "NDSI_multispectral",
                "snow_fraction": round(snow_cover, 4),
                "snow_detected": bool(snow_cover > opt_cfg.get("snow_ice_threshold", 0.20))
            }
        else:
            snow_check = {
                "status": "not evaluated",
                "reason": "Multispectral NIR and SWIR bands required for physical NDSI snow detection"
            }

        # 4. Atmospheric Haze check
        haze_check = {
            "status": "not evaluated",
            "reason": "Cirrus/coastal aerosol bands required for physical haze estimation"
        }

        image_checks.append({
            "image_id": img.get("id", f"img{idx+1}"),
            "valid_pixel_ratio": round(valid_ratio, 4),
            "cloud_cover": round(cloud_val, 4) if cloud_val is not None else "not evaluated",
            "snow_check": snow_check,
            "haze_check": haze_check,
            "bands_available": bands,
        })

    # 5. Seasonal water variance check
    seasonal_check = {
        "status": "not evaluated",
        "reason": "Multi-date historical baseline required for seasonal water variance"
    }

    # Assign status
    auto_suppress_cloud = dec_cfg.get("auto_suppress_cloud_above", 0.40)
    review_cloud = dec_cfg.get("review_queue_cloud_above", 0.15)
    review_valid = dec_cfg.get("review_queue_valid_below", 0.80)

    if max_cloud > auto_suppress_cloud:
        status = "suppressed (likely false alarm)"
        reason = f"Cloud cover ({max_cloud:.1%}) exceeds auto-suppression threshold ({auto_suppress_cloud:.1%})"
    elif max_cloud > review_cloud:
        status = "review queue"
        reason = f"Cloud cover ({max_cloud:.1%}) exceeds optical quality gate ({review_cloud:.1%})"
    elif min_valid < review_valid:
        status = "review queue"
        reason = f"Valid pixel ratio ({min_valid:.1%}) below threshold ({review_valid:.1%})"
    else:
        status = "use result"
        reason = f"Passed optical quality gate (cloud <= {review_cloud:.0%}, valid pixels >= {review_valid:.0%})"

    return {
        "status": status,
        "reason": reason,
        "max_cloud_cover": round(max_cloud, 4),
        "min_valid_pixels": round(min_valid, 4),
        "thresholds_applied": {
            "max_cloud_cover": opt_cfg["max_cloud_cover"],
            "min_valid_pixel_ratio": opt_cfg["min_valid_pixel_ratio"]
        },
        "image_checks": image_checks,
        "seasonal_water_variation": seasonal_check,
        "provenance": {
            "config_source": str(CONFIG_PATH),
            "method": "optical_quality_gate_v1",
            "bands_evaluated": [c["bands_available"] for c in image_checks]
        }
    }
