"""Ночной оркестратор цен v2: round-robin, кулдаун 48ч, медиана WB+Ozon, гарды."""
from __future__ import annotations
import csv, json, random, statistics, sys, time
from datetime import date
from pathlib import Path
import collectors as C

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
HIST = ROOT / "data" / "processed" / "price_history.csv"

# --- ADAPTER: сопоставить имена с src/config.py (логика ниже НЕ трогается) ---
from src.config import WB_QUERY, DOSE_PER_DAY, UNITS_PER_PACK  # noqa: E402


def query_of(sid: str):
    return WB_QUERY.get(sid)


def monthly(price_pack: float, sid: str):
    dose, pack = DOSE_PER_DAY.get(sid), UNITS_PER_PACK.get(sid)
    if not dose or not pack:
        return None
    return round(price_pack / pack * dose * 30, 1)


def median_price(wb, oz):
    if wb and oz:
        lo, hi = min(wb, oz), max(wb, oz)
        if hi > lo * 1.4:
            return wb, "wb", True
        return statistics.median([wb, oz]), "wb+ozon", False
    if wb:
        return wb, "wb", False
    if oz:
        return oz, "ozon", False
    return None, None, False


def jump_ok(old, new) -> bool:
    return old in (None, 0) or new is None or 1 / 3 <= new / old <= 3


def load_history() -> dict:
    last = {}
    if HIST.exists():
        with HIST.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last[row["id"]] = row["date"]
    return last


def main(limit: int = 27) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    last = load_history()
    today = date.today().isoformat()
    queue = sorted(data, key=lambda s: (s.get("price") is not None,
                                        last.get(s["id"], "0000")))
    flags, nulls, done = [], [], 0
    HIST.parent.mkdir(parents=True, exist_ok=True)
    with HIST.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if not HIST.stat().st_size:
            w.writerow(["date", "id", "wb", "ozon", "median", "source"])
        for s in queue[:limit]:
            sid, q = s["id"], query_of(sid)
            if not q:
                continue
            if last.get(sid) and (date.fromisoformat(today) -
                                  date.fromisoformat(last[sid])).days < 2:
                continue
            wb = oz = None
            try:
                offs = C.collect_wb(q)
                wb = monthly(statistics.median([o.price_rub for o in offs]), sid) if offs else None
            except C.CollectorError:
                pass
            time.sleep(1 + random.uniform(0, 1))
            try:
                offs = C.collect_ozon(q)
                oz = monthly(statistics.median([o.price_rub for o in offs]), sid) if offs else None
            except C.CollectorError:
                pass
            price, src, flag = median_price(wb, oz)
            if flag:
                flags.append(sid)
            if price is not None and not jump_ok(s.get("price"), price):
                flags.append(f"{sid}:JUMP")
                price = s.get("price")
            if price is not None:
                s["price"], s["price_source"] = price, src
            else:
                nulls.append(sid)
            w.writerow([today, sid, wb or "", oz or "", price or "", src or ""])
            done += 1
            time.sleep(1 + random.uniform(0, 1))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"обработано={done} null={nulls} флаги={flags}")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 27))
