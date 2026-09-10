import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
SNAP = ROOT / "tests" / "snapshot_data.json"


def test_snapshot_unchanged():
    cur = json.loads(DATA.read_text(encoding="utf-8"))
    if os.environ.get("UPDATE_SNAPSHOT") == "1" or not SNAP.exists():
        SNAP.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
        return  # первый прогон / осознанное обновление — создали слепок
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    assert cur == snap, (
        "data.json изменился относительно слепка! "
        "Если это осознанно: UPDATE_SNAPSHOT=1 python -m pytest tests/ -q"
    )