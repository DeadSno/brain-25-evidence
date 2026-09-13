"""Сборка контента топ-10 для 15 блоков в docs/data.json из src/content.py (v2.3.1).

Читает EDU_TOP10 из content.py, прокидывает 8 текстовых полей
(about/who_needs/onset/upper_limit/food_sources/guidelines/how_to_choose/myths)
в карточки data.json по каноничному id. Поля g/key_sources не трогаются (цикл 4).
Запуск:
    python scripts/build_edu.py
Идемпотентно: перезапуск не дублирует поля (поле есть — пропуск).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import content

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

EDU_FIELDS = ["about", "who_needs", "onset", "upper_limit",
              "food_sources", "guidelines", "how_to_choose", "myths"]


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in data}

    attached = 0
    skipped = 0
    missing = []
    for key, fields in content.EDU_TOP10.items():
        if key not in by_id:
            missing.append(key)
            continue
        card = by_id[key]
        if all(f in card for f in EDU_FIELDS):
            skipped += 1
            continue
        for f in EDU_FIELDS:
            card[f] = fields[f]
        attached += 1

    print(f"edu attached: {attached} cards (skipped already-filled: {skipped})")
    if missing:
        print(f"WARNING: нет карточек для id: {missing}")

    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print("data.json updated")


if __name__ == "__main__":
    main()