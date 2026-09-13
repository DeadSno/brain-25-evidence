"""Сборка interactions/synergists/antagonists в docs/data.json из src/content.py (v2.3).

Читает INTERACTIONS, SYNERGISTS, ANTAGONISTS из content.py, прокидывает поля
в карточки data.json по каноничному id (через INTERACTIONS_ALIAS). Добавки без
записей получают low-блок «известных взаимодействий нет». Запуск:
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

LOW_BLOCK = {"with": "", "severity": "low", "note": "известных взаимодействий нет"}


def resolve(key: str, ids: set[str]) -> str | None:
    if key in ids:
        return key
    return content.INTERACTIONS_ALIAS.get(key, None)


def attach_pairs(data: list[dict], ids: set[str], mapping: dict[str, list[str]], field: str) -> None:
    by_id = {d["id"]: d for d in data}
    attached = 0
    for key, partners in mapping.items():
        target = resolve(key, ids)
        if target is None or target not in by_id:
            continue
        card = by_id[target]
        if field in card:
            continue
        names = []
        for p in partners:
            rp = resolve(p, ids)
            names.append(rp if rp is not None else p)
        card[field] = names
        attached += 1
    print(f"{field}: {attached} cards")


def attach_interactions(data: list[dict], ids: set[str]) -> None:
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
    missing = [d["id"] for d in data if "interactions" not in d]
    for mid in missing:
        by_id[mid]["interactions"] = [LOW_BLOCK]
    print(f"interactions attached: {len(attached)} cards + low-block: {len(missing)}")
    print(f"candidates (без карточки): {len(content.INTERACTIONS_CANDIDATES)}")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ids = {d["id"] for d in data}

    attach_interactions(data, ids)
    attach_pairs(data, ids, content.ANTAGONISTS, "antagonists")
    attach_pairs(data, ids, content.SYNERGISTS, "synergists")

    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print("data.json updated")


if __name__ == "__main__":
    main()