"""Финализация черновиков: _drafts.json → data.json (инкрементально).

Мерджит только валидные карточки, оставляет остальные в _drafts.json.
Когда все готовы — _drafts.json становится пустым [].

Использование:
    python scripts\\apply_drafts.py            # применить готовые
    python scripts\\apply_drafts.py --check    # только показать что готово
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
DRAFTS = ROOT / "docs" / "_drafts.json"

REQUIRED_FIELDS = [
    "verdict", "dosage", "course", "caution", "about", "who_needs",
    "onset", "upper_limit", "food_sources", "guidelines",
    "how_to_choose", "myths", "grade",
]
PLACEHOLDER = "_пусто_"
VALID_GRADES = {"A", "B", "C", "D"}
VALID_CODES = {-1, 0, 1}


def validate(card: dict) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        v = card.get(f)
        if v is None or v == "" or v == PLACEHOLDER:
            errors.append(f"{f}: не заполнено")
    if not card.get("effects"):
        errors.append("effects: пусто")
    if not card.get("mechs"):
        errors.append("mechs: пусто (нужно 3-4 механизма)")
    if card.get("code") not in VALID_CODES:
        errors.append(f"code: {card.get('code')!r} (нужно -1 / 0 / 1)")
    if card.get("grade") not in VALID_GRADES:
        errors.append(f"grade: {card.get('grade')!r} (A / B / C / D)")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="только показать статус, не мерджить")
    args = ap.parse_args()

    if not DRAFTS.exists():
        print(f"[OK] {DRAFTS.name} не существует — нечего финализировать")
        return 0

    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
    if not drafts:
        print("[OK] _drafts.json пуст (всё готово)")
        return 0

    ready: list[dict] = []
    not_ready: list[tuple[str, list[str]]] = []

    for card in drafts:
        errs = validate(card)
        if errs:
            not_ready.append((card["id"], errs))
        else:
            ready.append(card)

    print(f"Готовы:   {len(ready)}")
    print(f"Не готовы: {len(not_ready)}")
    print()

    if not_ready:
        print("НЕ ГОТОВЫ:")
        for name, errs in not_ready:
            print(f"  {name}:")
            for e in errs[:3]:
                print(f"    - {e}")
            if len(errs) > 3:
                print(f"    ... ещё {len(errs) - 3}")
        print()

    if not ready:
        print("[INFO] Нет готовых карточек для мерджа")
        return 0

    if args.check:
        print(f"[CHECK] Готово к мерджу: {len(ready)}")
        for card in ready:
            print(f"  + {card['id']} (grade {card['grade']})")
        return 0

    # Мерджим готовые
    data = json.loads(DATA.read_text(encoding="utf-8"))
    existing_ids = {c["id"] for c in data}

    to_merge = [c for c in ready if c["id"] not in existing_ids]
    already = [c["id"] for c in ready if c["id"] in existing_ids]

    if already:
        print(f"[WARN] Уже в data.json (пропущены): {already}")

    if not to_merge:
        print("[INFO] Нечего мерджить (все уже в data.json)")
    else:
        shutil.copy(DATA, str(DATA) + ".bak")
        data.extend(to_merge)
        DATA.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] data.json → {len(data)} карточек (+{len(to_merge)})")
        for c in to_merge:
            print(f"    + {c['id']} (grade {c['grade']})")

    # Оставляем в _drafts.json только неготовые
    if not_ready:
        DRAFTS.write_text(
            json.dumps([c for c in drafts if c["id"] in {n for n, _ in not_ready}],
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] _drafts.json → {len(not_ready)} остаётся")
    else:
        DRAFTS.unlink()
        print(f"[OK] _drafts.json удалён (все готовы)")

    print()
    print("Дальше:")
    print("  python scripts\\update_all.py --apply    # подтянет scienceIndex/g/citations")
    print("  python scripts\\build_index.py")
    print("  $env:UPDATE_SNAPSHOT='1'; python -m pytest tests/test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT")
    print("  python -m pytest -q -m 'not network'")
    return 0


if __name__ == "__main__":
    sys.exit(main())