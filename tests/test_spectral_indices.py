import numpy as np
import pytest

from gateway.spectral_indices import compute_spectral_indices


def test_rgb_image_returns_not_available():
    # 3-channel RGB image (red, green, blue) — typical drone/satellite web upload
    arr = np.full((3, 64, 64), 0.4, dtype=np.float32)
    img = {
        "id": "img1",
        "bands": ["red", "green", "blue"],
        "array": arr,
        "modality": "optical",
    }
    res = compute_spectral_indices(img)
    assert res["status"] == "not available"
    assert res["reason"] == "Spectral indices not available for RGB image"
    assert "nir" in res["missing_bands"]
    assert res["indices"]["ndvi"]["status"] == "not available"
    assert res["indices"]["ndvi"]["value"] is None
    assert res["indices"]["ndwi"]["status"] == "not available"
    assert res["indices"]["ndwi"]["value"] is None


def test_multispectral_indices_computed_accurately():
    # 5-band multispectral image: [red, green, blue, nir, swir]
    arr = np.zeros((5, 10, 10), dtype=np.float32)
    arr[0] = 0.1  # red = 0.1
    arr[1] = 0.2  # green = 0.2
    arr[2] = 0.15 # blue = 0.15
    arr[3] = 0.5  # nir = 0.5
    arr[4] = 0.05 # swir = 0.05

    img = {
        "id": "img1",
        "bands": ["red", "green", "blue", "nir", "swir"],
        "array": arr,
        "modality": "optical",
    }
    res = compute_spectral_indices(img)
    assert res["status"] == "available"

    # Expected NDVI: (0.5 - 0.1) / (0.5 + 0.1) = 0.4 / 0.6 = 0.6667
    assert res["indices"]["ndvi"]["status"] == "available"
    assert abs(res["indices"]["ndvi"]["mean"] - 0.6667) < 1e-3
    assert res["indices"]["ndvi"]["vegetation_fraction"] == 1.0

    # Expected NDWI: (0.2 - 0.5) / (0.2 + 0.5) = -0.3 / 0.7 = -0.4286
    assert res["indices"]["ndwi"]["status"] == "available"
    assert abs(res["indices"]["ndwi"]["mean"] - (-0.4286)) < 1e-3
    assert res["indices"]["ndwi"]["water_fraction"] == 0.0


def test_single_band_or_empty_returns_not_available():
    img = {"id": "img1", "bands": ["gray"], "array": np.ones((1, 10, 10), dtype=np.float32)}
    res = compute_spectral_indices(img)
    assert res["status"] == "not available"
    assert "nir" in res["missing_bands"]
