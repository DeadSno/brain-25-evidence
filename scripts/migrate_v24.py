"""Схема v2.4: nullable-поля доказательности в docs/data.json.
Добавляет пустые hedges_g/hedges_g_ci/effect_outcome/grade/key_sources всем
карточкам (пустые = «данных пока нет»; значения заполняются только после
«ок» владельца в docs/approve_queue.md). Идемпотентно: уже заполненные не трогает.
Запуск: python scripts/migrate_v24.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

V24_FIELDS = {
    "hedges_g": None,
    "hedges_g_ci": None,
    "effect_outcome": None,
    "grade": None,
    "key_sources": [],
}


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for card in data:
        for k, v in V24_FIELDS.items():
            if k not in card:
                card[k] = v
    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print(f"v2.4 schema: {len(data)} cards, {len(V24_FIELDS)} nullable fields")


if __name__ == "__main__":
    main()