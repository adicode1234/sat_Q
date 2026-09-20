"""Exercise demo-only trainers without promoting synthetic weights to real imagery."""
import json
from pathlib import Path
from training.train_tiny import main as tiny
from training.train_fusion import main as fusion
ROOT=Path(__file__).resolve().parents[1]
paths=['models/checkpoints/rgb_base.npz','models/checkpoints/rgb_adapter.npz','models/checkpoints/fusion_cross_attention/weights.pt','models/checkpoints/fusion_cross_attention/config.json']
saved={p:(ROOT/p).read_bytes() for p in paths}
try:
    tiny();fusion()
    result={'tiny_rgb':json.loads((ROOT/'training/before_after.json').read_text()),'synthetic_fusion':json.loads((ROOT/'training/fusion_before_after.json').read_text()),'promoted':False,'reason':'Synthetic-only training is a demo check, not real-image improvement. Original checkpoints retained.'}
    (ROOT/'training/demo_training_results.json').write_text(json.dumps(result,indent=2))
finally:
    for p,data in saved.items():(ROOT/p).write_bytes(data)
