import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import EN


def test_data_and_config_in_sync():
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    ids = {s["id"] for s in data}
    cfg = set(EN.keys())
    assert ids == cfg, (
        f"расхождение data.json ↔ config.py: "
        f"только в data={sorted(ids - cfg)}, только в config={sorted(cfg - ids)}"
    )