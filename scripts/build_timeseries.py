"""Собирает data/timeseries/*.json → docs/timeseries.json — единый файл для фронта."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "timeseries"
DST = ROOT / "docs" / "timeseries.json"

SOURCES = ["pubmed", "wiki", "citations"]

out: dict = {"_meta": {"sources": SOURCES}}
for s in SOURCES:
    p = SRC / f"{s}.json"
    if p.exists():
        out[s] = json.loads(p.read_text(encoding="utf-8"))
        print(f"[OK] {s}: {len(out[s])} карточек")
    else:
        print(f"[SKIP] {s}: не найден")

DST.write_text(
    json.dumps(out, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print(f"[OK] {DST} — {DST.stat().st_size / 1024:.0f} KB")