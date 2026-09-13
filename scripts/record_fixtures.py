"""Одноразовая запись реальных ответов API в фикстуры (слой L2)."""
import json
from pathlib import Path
from urllib.parse import quote
import collectors as C

FIX = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)
wb = C._get(C.WB_URL, {"appType": 1, "curr": "rub", "dest": -1257786,
                       "query": "креатин моногидрат", "resultset": "catalog",
                       "sort": "popular"})
oz = C._get(C.OZON_URL, {"url": f"/search/?text={quote('креатин')}"})
(FIX / "wb_creatine.json").write_text(json.dumps(wb, ensure_ascii=False), encoding="utf-8")
(FIX / "ozon_creatine.json").write_text(json.dumps(oz, ensure_ascii=False), encoding="utf-8")
print("fixtures saved:", sorted(p.name for p in FIX.glob("*.json")))
