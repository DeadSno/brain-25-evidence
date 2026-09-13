"""Парсер суточных доз (в день) из docs/data.json: мес-лексика поля dosage."""
from __future__ import annotations
import json, re, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

# первое вхождение "N г", "N-M г", "N.5 г" (порошки: доза в граммах/день)
_GR = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*[-\u2013\u2014]\s*(\d+(?:[.,]\d+)?)\s*г\b"
    r"|\b(\d+(?:[.,]\d+)?)\s*г\b", re.I)


def parse_grams_day(text: str) -> float | None:
    m = _GR.search(text or "")
    if not m:
        return None
    if m.group(1):
        lo = float(m.group(1).replace(",", "."))
        hi = float(m.group(2).replace(",", "."))
        return round((lo + hi) / 2, 2)
    return float(m.group(3).replace(",", "."))


def monthly(price_pack: float, units_pack: float, sid: str,
            dose: float | None = None) -> float | None:
    d = dose if dose is not None else DOSE_PER_DAY.get(sid)
    if not price_pack or not units_pack or not d:
        return None
    return round(price_pack / units_pack * d * 30, 1)


def build_doses() -> tuple[dict[str, float], dict[str, str]]:
    """Доза на день: г — из dosage-текста; капс/табл — NORM/30 (помечается)."""
    from src.config import WB_QUERY, NORM
    data = {s["id"]: s.get("dosage") or "" for s in json.loads(DATA.read_text(encoding="utf-8"))}
    doses, flags = {}, {}
    for sid, (_q, unit) in WB_QUERY.items():
        if unit == "г":
            v = parse_grams_day(data.get(sid, ""))
            if v:
                doses[sid] = v
                flags[sid] = "parsed:г"
                continue
        norm = NORM.get(sid, 30)
        doses[sid] = round(norm / 30.0, 2)
        flags[sid] = f"default:{norm}/30"
    return doses, flags


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    doses, flags = build_doses()
    for sid, v in doses.items():
        print(f"{sid:26} {v:>6}  [{flags[sid]}]")

DOSE_PER_DAY, DOSE_FLAGS = build_doses()


def cmd_units_csv() -> None:
    """Подсказка для approve-таблицы: 10 показателей дозировки."""
    sys_stdout = __import__("sys").stdout
    sys_stdout.reconfigure(encoding="utf-8")
    data = {s["id"]: s.get("dosage") or "" for s in json.loads(DATA.read_text(encoding="utf-8"))}
    for sid in list(DOSE_PER_DAY)[:10]:
        print(f"{sid} | текст: {data.get(sid,'')[:50]:52} | доза/сут: {DOSE_PER_DAY[sid]} | {DOSE_FLAGS[sid]}")