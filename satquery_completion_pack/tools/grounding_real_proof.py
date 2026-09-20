import json
import time
from pathlib import Path

import requests


ROOT = Path(".").resolve()
BASE = "http://127.0.0.1:8000"

IMAGE = ROOT / "data" / "vrsbench" / "P0003_0002.png"

OUT = ROOT / "docs" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

if not IMAGE.exists():
    raise SystemExit(f"Missing image: {IMAGE}")


queries = [
    ("water_a", "Locate the water."),
    ("water_b", "Where is the water body?"),
    ("water_c", "Highlight the surface water."),
    ("building", "Locate the buildings."),
    ("road", "Locate the road."),
    ("forest", "Locate the forest."),
]


def get_boxes(job):
    result = job.get("result") or {}
    overlay = result.get("overlay") or {}

    if overlay.get("type") != "bbox":
        return []

    boxes = []

    for item in overlay.get("data") or []:
        if not isinstance(item, dict):
            continue

        box = item.get("box")

        if box and len(box) == 4:
            boxes.append({
                "box": [float(x) for x in box],
                "label": item.get("label"),
                "score": item.get("score"),
            })

    return boxes


def iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)

    aa = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    bb = max(0, b[2] - b[0]) * max(0, b[3] - b[1])

    return inter / max(aa + bb - inter, 1e-9)


rows = []

for key, query in queries:

    print("\n" + "=" * 80)
    print("QUERY:", query)

    with IMAGE.open("rb") as f:

        files = {
            "images": (
                IMAGE.name,
                f,
                "image/png"
            )
        }

        options = [{
            "modality": "optical",
            "bands": ["red", "green", "blue"],
            "benchmark_source": "VRSBench public evaluation image"
        }]

        data = {
            "scenario": "SINGLE",
            "query": query,
            "options": json.dumps(options)
        }

        response = requests.post(
            BASE + "/api/jobs",
            files=files,
            data=data,
            timeout=60
        )

        response.raise_for_status()

        job_id = response.json()["job_id"]

    job = None

    for _ in range(120):

        time.sleep(2)

        r = requests.get(
            BASE + f"/api/jobs/{job_id}",
            timeout=30
        )

        r.raise_for_status()

        job = r.json()

        if job.get("status") not in {
            "queued",
            "validating",
            "running",
            "verifying"
        }:
            break

    result = job.get("result") or {}
    decision = result.get("decision")

    row = {
        "key": key,
        "query": query,
        "job_id": job_id,
        "status": job.get("status"),
        "task": result.get("task"),
        "decision":
            decision.get("status")
            if isinstance(decision, dict)
            else decision,
        "boxes": get_boxes(job)
    }

    rows.append(row)

    print(json.dumps(row, indent=2))


# ----------------------------------------------------------
# METRICS
# ----------------------------------------------------------

water_rows = [
    row for row in rows
    if row["key"].startswith("water_")
    and row["boxes"]
]

water_ious = []

for i in range(len(water_rows)):
    for j in range(i + 1, len(water_rows)):

        water_ious.append(
            iou(
                water_rows[i]["boxes"][0]["box"],
                water_rows[j]["boxes"][0]["box"]
            )
        )


water_mean_iou = (
    sum(water_ious) / len(water_ious)
    if water_ious
    else None
)


contrast = {}

if water_rows:

    water_box = water_rows[0]["boxes"][0]["box"]

    for row in rows:

        if row["key"] in {
            "building",
            "road",
            "forest"
        } and row["boxes"]:

            contrast[row["key"]] = iou(
                water_box,
                row["boxes"][0]["box"]
            )


all_complete = all(
    row["status"] == "complete"
    for row in rows
)

different_semantic_region = any(
    value < 0.95
    for value in contrast.values()
)


proof = {
    "generated_at":
        time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        ),

    "image":
        str(IMAGE.relative_to(ROOT)),

    "dataset":
        "VRSBench",

    "rows":
        rows,

    "water_paraphrase_mean_iou":
        water_mean_iou,

    "water_vs_other_iou":
        contrast,

    "all_jobs_complete":
        all_complete,

    "query_sensitive":
        different_semantic_region,

    "conclusion":
        (
            "Grounding is text-conditioned: "
            "semantically different prompts produced "
            "different spatial predictions."
            if different_semantic_region
            else
            "Query sensitivity was not demonstrated."
        )
}


json_path = (
    OUT /
    "GROUNDING_QUERY_SENSITIVITY_PROOF.json"
)

json_path.write_text(
    json.dumps(proof, indent=2),
    encoding="utf-8"
)


md = [
    "# Grounding Query-Sensitivity Proof",
    "",
    f"Dataset: **VRSBench**",
    "",
    f"Image: `{proof['image']}`",
    "",
    "## Queries",
    "",
    "| Query | Status | Boxes |",
    "|---|---|---:|",
]

for row in rows:

    md.append(
        f"| {row['query']} | "
        f"{row['status']} | "
        f"{len(row['boxes'])} |"
    )


md += [
    "",
    "## Spatial consistency",
    "",
    (
        "Mean IoU among water paraphrases: "
        f"**{water_mean_iou}**"
    ),
    "",
    (
        "Water vs semantic contrast IoUs: "
        f"`{contrast}`"
    ),
    "",
    "## Conclusion",
    "",
    proof["conclusion"],
    "",
    (
        "The earlier synthetic demo GeoTIFF produced "
        "whole-image detections and is therefore not "
        "used as evidence of grounding quality."
    )
]


md_path = (
    OUT /
    "GROUNDING_QUERY_SENSITIVITY_PROOF.md"
)

md_path.write_text(
    "\n".join(md),
    encoding="utf-8"
)


print("\n" + "=" * 80)
print("FINAL GROUNDING PROOF")
print("=" * 80)

print(
    json.dumps(
        {
            "all_jobs_complete":
                all_complete,

            "water_paraphrase_mean_iou":
                water_mean_iou,

            "water_vs_other_iou":
                contrast,

            "query_sensitive":
                different_semantic_region
        },
        indent=2
    )
)


if not all_complete:
    raise SystemExit(
        "FAIL: one or more production jobs failed"
    )

if not different_semantic_region:
    raise SystemExit(
        "FAIL: semantic contrast did not change localization"
    )

print(
    "\n[PASS] Text-conditioned grounding "
    "demonstrated on a real VRSBench image."
)
