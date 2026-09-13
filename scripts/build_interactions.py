"""Сборка interactions в docs/data.json из src/content.py (v2.2).

Читает INTERACTIONS + INTERACTIONS_ALIAS из content.py, прокидывает поле
interactions в карточки data.json по каноничному id. Запуск:
    python scripts/build_interactions.py
Идемпотентно: перезапуск не дублирует поле.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import content

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"


def resolve(key: str, ids: set[str]) -> str | None:
    if key in ids:
        return key
    return content.INTERACTIONS_ALIAS.get(key, None)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ids = {d["id"] for d in data}
    by_id = {d["id"]: d for d in data}

    attached: set[str] = set()
    for key, items in content.INTERACTIONS.items():
        target = resolve(key, ids)
        if target is None:
            continue
        card = by_id[target]
        if "interactions" in card:
            continue
        card["interactions"] = items
        attached.add(target)

    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print(f"interactions attached: {len(attached)} cards")
    print(f"candidates (без карточки): {len(content.INTERACTIONS_CANDIDATES)}")


if __name__ == "__main__":
    main()