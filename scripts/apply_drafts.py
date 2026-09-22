"""Финализация черновиков: _drafts.json → data.json.

Проверяет, что все обязательные поля заполнены (не '_пусто_'),
мерджит карточки в data.json и удаляет _drafts.json.

Использование:
    python scripts\\apply_drafts.py
    python scripts\\apply_drafts.py --keep      # не удалять _drafts.json
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


def validate(card: dict) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        v = card.get(f)
        if v is None or v == "" or v == PLACEHOLDER:
            errors.append(f"{f}: не заполнено")
    if not card.get("effects"):
        errors.append("effects: пусто")
    if not card.get("mechs"):
        errors.append("mechs: пусто (3-4 механизма)")
    if card.get("code") not in (-1, 0, 1):
        errors.append(f"code: {card.get('code')} (нужно -1 / 0 / 1)")
    if card.get("grade") not in ("A", "B", "C", "D"):
        if card.get("grade") != PLACEHOLDER:
            errors.append(f"grade: {card.get('grade')} (A / B / C / D)")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="не удалять _drafts.json")
    args = ap.parse_args()

    if not DRAFTS.exists():
        print(f"[OK] {DRAFTS.name} не существует — нечего финализировать")
        return 0

    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
    if not drafts:
        print("[OK] _drafts.json пуст")
        return 0

    print(f"Черновиков: {len(drafts)}\n")

    all_errors: dict[str, list[str]] = {}
    for card in drafts:
        errors = validate(card)
        if errors:
            all_errors[card["id"]] = errors

    if all_errors:
        print("[FAIL] Найдены незаполненные поля:\n")
        for name, errors in all_errors.items():
            print(f"  {name}:")
            for e in errors:
                print(f"    - {e}")
        print(f"\nЗаполни и запусти снова.")
        return 1

    # Все валидны — мерджим
    data = json.loads(DATA.read_text(encoding="utf-8"))
    existing_ids = {c["id"] for c in data}
    to_merge = [c for c in drafts if c["id"] not in existing_ids]
    duplicates = [c["id"] for c in drafts if c["id"] in existing_ids]

    if duplicates:
        print(f"[WARN] Уже в data.json (пропущены): {duplicates}")

    shutil.copy(DATA, str(DATA) + ".bak")
    data.extend(to_merge)
    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] data.json → {len(data)} карточек (+{len(to_merge)})")

    if not args.keep:
        DRAFTS.unlink()
        print(f"[OK] {DRAFTS.name} удалён")

    print()
    print("Дальше:")
    print("  1. python scripts\\update_all.py --apply")
    print("  2. python scripts\\build_index.py")
    print("  3. $env:UPDATE_SNAPSHOT='1'; python -m pytest tests/test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT")
    print("  4. python -m pytest -q -m 'not network'")
    return 0


if __name__ == "__main__":
    sys.exit(main())