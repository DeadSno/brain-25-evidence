"""Удаляет мёртвые поля из docs/data.json.

Мёртвые поля — те, что никто не читает в script.js.
После удаления snapshot-тест надо обновить.

Запуск:
    python scripts/cleanup_dead_fields.py --dry-run
    python scripts/cleanup_dead_fields.py --apply
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"

DEAD_FIELDS = [
    "reviews",
    "trends",
    "pubmed_term",
    "effect_outcome",
    "year_last_ma",
    "who",
    "ul",
    "food",
    "official",
    "hedges_g_ci",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="записать изменения")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    # Инвентаризация
    present = {f: 0 for f in DEAD_FIELDS}
    for c in data:
        for f in DEAD_FIELDS:
            if f in c:
                present[f] += 1

    print("Поля к удалению (сколько карточек содержат):")
    for f in DEAD_FIELDS:
        mark = "✓" if present[f] else "·"
        print(f"  {mark} {f:20s} {present[f]:3d}/81")

    total = sum(present.values())
    print(f"\nВсего полей к удалению: {total}")

    if total == 0:
        print("Нечего удалять.")
        return 0

    # Удаляем
    for c in data:
        for f in DEAD_FIELDS:
            c.pop(f, None)

    # Проверка, что не осталось мёртвых
    still = set()
    for c in data:
        still.update(c.keys() & set(DEAD_FIELDS))
    if still:
        print(f"[!] остались: {sorted(still)}")
        return 1

    print("\nВсе удаляемые поля вычищены.")

    if args.apply:
        # Бэкап
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = DATA_JSON.with_suffix(f".json.bak-{ts}")
        shutil.copy2(DATA_JSON, backup)

        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Бэкап:   {backup.name}")
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print("[dry-run] данные не записаны. Добавьте --apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())