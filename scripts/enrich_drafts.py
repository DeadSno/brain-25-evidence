"""Обогащает docs/_drafts.json из proposal.

Читает reports/q14_batch_N_proposal.json, обновляет карточки в
_drafts.json (только те id, что есть в proposal). Остальные не трогает.

Использование:
    python scripts/enrich_drafts.py --proposal q14_batch_14_proposal.json
    python scripts/enrich_drafts.py --proposal q14_batch_14_proposal.json --apply
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "docs" / "_drafts.json"
PROPOSAL_DIR = ROOT / "reports"

# Поля, которые proposal может обновить в _drafts.json
ENRICH_FIELDS = [
    # базовые
    "verdict", "grade", "code",
    "dosage", "course", "caution", "upper_limit",
    # adv
    "about", "who_needs", "onset", "myths",
    "food_sources", "guidelines", "how_to_choose",
    # структура
    "effects", "mechs", "key_sources",
]

# Валидация длин adv-полей (совпадает с apply_adv.py)
LIMITS = {
    "about":         (30, 160),
    "who_needs":     (40, 180),
    "onset":         (30, 150),
    "myths":         (60, 220),
    "food_sources":  (25, 180),
    "guidelines":    (40, 180),
    "how_to_choose": (35, 180),
}

VALID_STRENGTH = {"сильно", "умеренно", "слабо", "контекст", "маркетинг"}
VALID_GRADES = {"A", "B", "C", "D"}
VALID_CODES = {-1, 0, 1}
VALID_VERDICTS = {"работает", "зависит от контекста", "не подтверждено"}


def validate_adv(card_id: str, card: dict) -> list[str]:
    errs = []
    for field, (lo, hi) in LIMITS.items():
        v = card.get(field, "")
        if not isinstance(v, str):
            errs.append(f"{card_id}.{field}: не строка")
            continue
        L = len(v.strip())
        if not (lo <= L <= hi):
            errs.append(f"{card_id}.{field}: {L} симв, нужно {lo}-{hi}")
    return errs


def validate_mechs(card_id: str, mechs: list) -> list[str]:
    errs = []
    if not isinstance(mechs, list) or not (2 <= len(mechs) <= 4):
        errs.append(f"{card_id}.mechs: нужно 2-4 штуки, есть {len(mechs) if isinstance(mechs, list) else '?'}")
        return errs
    for i, m in enumerate(mechs):
        if not isinstance(m, list) or len(m) != 3:
            errs.append(f"{card_id}.mechs[{i}]: не [механизм, эффект, сила]")
            continue
        mm, ef, st = m
        if not isinstance(mm, str) or not (20 <= len(mm) <= 250):
            errs.append(f"{card_id}.mechs[{i}].механизм: {len(mm) if isinstance(mm, str) else '?'} симв (20-250)")
        if not isinstance(ef, str) or not (5 <= len(ef) <= 120):
            errs.append(f"{card_id}.mechs[{i}].эффект: {len(ef) if isinstance(ef, str) else '?'} симв (5-120)")
        if st not in VALID_STRENGTH:
            errs.append(f"{card_id}.mechs[{i}].сила: {st!r} не из {VALID_STRENGTH}")
    return errs


def validate_simple(card_id: str, card: dict) -> list[str]:
    errs = []
    if card.get("grade") not in VALID_GRADES:
        errs.append(f"{card_id}.grade: {card.get('grade')!r}")
    if card.get("code") not in VALID_CODES:
        errs.append(f"{card_id}.code: {card.get('code')!r}")
    if card.get("verdict") not in VALID_VERDICTS:
        errs.append(f"{card_id}.verdict: {card.get('verdict')!r}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", required=True, type=Path,
                    help="Имя файла в reports/ (например, q14_batch_14_proposal.json)")
    ap.add_argument("--apply", action="store_true",
                    help="Записать изменения в _drafts.json")
    args = ap.parse_args()

    if not args.proposal.is_absolute():
        args.proposal = PROPOSAL_DIR / args.proposal

    if not args.proposal.exists():
        print(f"[ERROR] Не найден: {args.proposal}", file=sys.stderr)
        return 1

    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))

    print(f"Proposal:  {args.proposal.name} ({len(proposal)} карточек)")
    print(f"Drafts:    {DRAFTS.name} ({len(drafts)} карточек)")
    print()

    # Индексы
    drafts_by_id = {c["id"]: c for c in drafts}

    # Валидация proposal
    all_errors = []
    for card_id, card in proposal.items():
        errs = []
        errs += validate_adv(card_id, card)
        errs += validate_mechs(card_id, card.get("mechs", []))
        errs += validate_simple(card_id, card)
        if errs:
            print(f"❌ {card_id}:")
            for e in errs:
                print(f"   {e}")
            all_errors += errs
        else:
            print(f"✅ {card_id}")

    if all_errors:
        print(f"\n[STOP] {len(all_errors)} ошибок валидации. Файл не изменён.")
        return 1

    # Проверка что все id есть в drafts
    missing_ids = [k for k in proposal if k not in drafts_by_id]
    if missing_ids:
        print(f"\n[WARN] Нет в _drafts.json: {missing_ids}")

    # Что обновим
    print("\n=== Обновления ===")
    for card_id, card in proposal.items():
        if card_id not in drafts_by_id:
            continue
        draft = drafts_by_id[card_id]
        updated_fields = []
        for field in ENRICH_FIELDS:
            if field not in card:
                continue
            new_val = card[field]
            old_val = draft.get(field)
            if new_val != old_val:
                updated_fields.append(field)
                if args.apply:
                    draft[field] = new_val
        print(f"  {card_id}: {', '.join(updated_fields) if updated_fields else 'нет изменений'}")

    if not args.apply:
        print("\n[DRY-RUN] Файл _drafts.json НЕ изменён. Для записи: --apply")
        return 0

    # Backup
    bak = DRAFTS.with_suffix(".json.bak")
    shutil.copy(DRAFTS, bak)
    print(f"\n[OK] Backup: {bak}")

    DRAFTS.write_text(
        json.dumps(drafts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] {DRAFTS} обновлён")

    # Сколько готовых
    from apply_drafts import validate as validate_full  # type: ignore
    ready = sum(1 for c in drafts if not validate_full(c))
    print(f"\nГотовых к apply_drafts.py: {ready}/{len(drafts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())