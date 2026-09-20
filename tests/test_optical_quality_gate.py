import numpy as np
import pytest
from fastapi.testclient import TestClient

from configs import *
from gateway.app import app
from gateway.optical_quality_gate import evaluate_optical_quality_gate, load_quality_config
from gateway.review_queue import (
    add_candidate,
    confirm_candidate,
    get_candidates,
    get_stats,
    reject_candidate,
)


def test_load_quality_config():
    cfg = load_quality_config()
    assert "optical" in cfg
    assert "decision_rules" in cfg
    assert cfg["optical"]["max_cloud_cover"] == 0.15
    assert cfg["optical"]["min_valid_pixel_ratio"] == 0.80


def test_gate_passes_for_clear_imagery():
    # Synthetic clear 3-band RGB image (no clouds, finite values)
    arr = np.full((3, 64, 64), 0.3, dtype=np.float32)
    bundle = {
        "images": [
            {"id": "img1", "array": arr, "bands": ["red", "green", "blue"]},
            {"id": "img2", "array": arr, "bands": ["red", "green", "blue"]},
        ]
    }
    result = evaluate_optical_quality_gate(bundle)
    assert result["status"] == "use result"
    assert result["max_cloud_cover"] <= 0.15
    assert result["min_valid_pixels"] >= 0.80
    assert "Passed optical quality gate" in result["reason"]


def test_gate_review_queue_for_moderate_cloud():
    # Image with ~25% bright neutral cloud pixels (between 15% and 40%)
    arr = np.full((3, 64, 64), 0.3, dtype=np.float32)
    arr[:, :32, :32] = 0.95  # 25% cloud
    bundle = {
        "images": [
            {"id": "img1", "array": arr, "bands": ["red", "green", "blue"]},
            {"id": "img2", "array": arr, "bands": ["red", "green", "blue"]},
        ]
    }
    result = evaluate_optical_quality_gate(bundle)
    assert result["status"] == "review queue"
    assert 0.15 < result["max_cloud_cover"] <= 0.40


def test_gate_auto_suppress_for_heavy_cloud():
    # Image with >50% bright neutral cloud pixels (>40%)
    arr = np.full((3, 64, 64), 0.3, dtype=np.float32)
    arr[:, :48, :] = 0.95  # 75% cloud
    bundle = {
        "images": [
            {"id": "img1", "array": arr, "bands": ["red", "green", "blue"]},
            {"id": "img2", "array": arr, "bands": ["red", "green", "blue"]},
        ]
    }
    result = evaluate_optical_quality_gate(bundle)
    assert result["status"] == "suppressed (likely false alarm)"
    assert result["max_cloud_cover"] > 0.40


def test_gate_review_queue_for_low_valid_pixels():
    # Image with 30% NaN / invalid pixels (valid = 70% < 80%)
    arr = np.full((3, 64, 64), 0.3, dtype=np.float32)
    arr[:, :20, :] = np.nan
    bundle = {
        "images": [
            {"id": "img1", "array": arr, "bands": ["red", "green", "blue"]},
            {"id": "img2", "array": arr, "bands": ["red", "green", "blue"]},
        ]
    }
    result = evaluate_optical_quality_gate(bundle)
    assert result["status"] == "review queue"
    assert result["min_valid_pixels"] < 0.80


def test_missing_bands_not_evaluated():
    # RGB-only image without NIR or SWIR
    arr = np.full((3, 64, 64), 0.3, dtype=np.float32)
    bundle = {
        "images": [
            {"id": "img1", "array": arr, "bands": ["red", "green", "blue"]},
            {"id": "img2", "array": arr, "bands": ["red", "green", "blue"]},
        ]
    }
    result = evaluate_optical_quality_gate(bundle)
    # Snow & Haze must be "not evaluated", not fake numbers
    for check in result["image_checks"]:
        assert check["snow_check"]["status"] == "not evaluated"
        assert check["haze_check"]["status"] == "not evaluated"
    assert result["seasonal_water_variation"]["status"] == "not evaluated"


def test_sqlite_review_queue_workflow():
    gate_mock = {
        "status": "review queue",
        "reason": "Cloud cover exceeds 15%",
        "max_cloud_cover": 0.22,
        "min_valid_pixels": 0.98,
        "provenance": {"method": "optical_quality_gate_v1"},
    }
    cand_id = add_candidate(
        analysis_id="test_analysis_123",
        query="Verify flood change",
        status="review queue",
        gate_summary=gate_mock,
        change_fraction=0.12,
        preview_before="/api/preview/test_123/0",
        preview_after="/api/preview/test_123/1",
    )
    assert isinstance(cand_id, str) and len(cand_id) == 32

    # Verify candidate is initially pending
    candidates = get_candidates(decision="pending")
    matched = next((c for c in candidates if c["candidate_id"] == cand_id), None)
    assert matched is not None
    assert matched["decision"] == "pending"
    assert matched["query"] == "Verify flood change"
    assert matched["status"] == "review queue"
    assert matched["cloud_fraction"] == 0.22

    # Analyst confirms
    ok = confirm_candidate(cand_id, analyst_notes="Confirmed river bank widening")
    assert ok is True

    # Verify status changed to confirmed
    confirmed_list = get_candidates(decision="confirmed")
    confirmed = next((c for c in confirmed_list if c["candidate_id"] == cand_id), None)
    assert confirmed is not None
    assert confirmed["decision"] == "confirmed"
    assert confirmed["analyst_notes"] == "Confirmed river bank widening"

    # Reject another candidate
    cand_id_2 = add_candidate(
        analysis_id="test_analysis_456",
        query="Check urban expansion",
        status="suppressed (likely false alarm)",
        gate_summary=gate_mock,
        change_fraction=0.35,
    )
    ok_reject = reject_candidate(cand_id_2, analyst_notes="False alarm due to cloud shadow")
    assert ok_reject is True
    rejected_list = get_candidates(decision="rejected")
    rejected = next((c for c in rejected_list if c["candidate_id"] == cand_id_2), None)
    assert rejected is not None
    assert rejected["decision"] == "rejected"

    stats = get_stats()
    assert stats["total"] >= 2
    assert stats["confirmed"] >= 1
    assert stats["rejected"] >= 1


def test_review_queue_api():
    client = TestClient(app)
    stats_res = client.get("/api/review-queue/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "pending" in stats
    assert "confirmed" in stats
    assert "rejected" in stats

    list_res = client.get("/api/review-queue")
    assert list_res.status_code == 200
    items = list_res.json()
    assert isinstance(items, list)

    html_res = client.get("/review-queue")
    assert html_res.status_code == 200
    assert "Analyst Review Queue" in html_res.text
