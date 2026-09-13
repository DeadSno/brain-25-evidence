"""Одноразовая запись реальных ответов API в фикстуры (tolerant, слой L2)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collectors as C

FIX = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)


def _save(name, payload):
    (FIX / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print("OK", name)


def main() -> int:
    # 1) wb_search — v5 через сессию с прогревом
    try:
        data = C._get(C.WB_URL_V5, {**C.WB_PARAMS, "query": "креатин моногидрат"})
        _save("wb_creatine.json", data)
    except C.CollectorError as e:
        print(f"SKIP wb_search: {e}")

    # 2) wb_basket — collect_wb с cached_id=4219394
    try:
        C._ID_CACHE["креатин"] = [4219394]
        offs = C.collect_wb("креатин")
        if not offs:
            raise C.CollectorError("нет офферов (search+basket молчат)")
        _save("wb_basket_creatine.json", [o.__dict__ for o in offs])
    except C.CollectorError as e:
        print(f"SKIP wb_basket: {e}")

    # 3) ozon
    try:
        offs = C.collect_ozon("креатин")
        _save("ozon_creatine.json", [o.__dict__ for o in offs])
    except C.CollectorError as e:
        print(f"SKIP ozon: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
