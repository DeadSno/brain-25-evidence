"""Универсальный валидатор q14_batch_N_proposal.json.

Запуск:
    python scripts/validate_proposal.py --proposal q14_batch_16_proposal.json

Проверяет:
- Все обязательные поля
- Длины adv-полей в диапазонах
- mechs 2-4 штуки, формат [механизм, эффект, сила]
- key_sources: year int, journal непустой
- interactions: у всех есть with
- effects: 5-40 симв
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_DIR = ROOT / "reports"

ADV_LIMITS = {
    "about": (30, 160),
    "who_needs": (40, 180),
    "onset": (30, 150),
    "myths": (60, 220),
    "food_sources": (25, 180),
    "guidelines": (40, 180),
    "how_to_choose": (35, 180),
}

REQUIRED = [
    "verdict", "grade", "code",
    "dosage", "course", "caution", "upper_limit",
    "about", "who_needs", "onset", "myths",
    "food_sources", "guidelines", "how_to_choose",
    "effects", "mechs", "key_sources", "interactions",
]

VALID_STRENGTH = {"сильно", "умеренно", "слабо", "контекст", "маркетинг"}
VALID_GRADES = {"A", "B", "C", "D"}
VALID_CODES = {-1, 0, 1}
VALID_VERDICTS = {"работает", "зависит от контекста", "не подтверждено"}


def validate_card(card_id: str, card: dict) -> list[str]:
    errors = []

    # Обязательные поля
    for f in REQUIRED:
        if f not in card:
            errors.append(f"{card_id}.{f}: отсутствует")

    # adv-поля
    for field, (lo, hi) in ADV_LIMITS.items():
        v = card.get(field, "")
        if not isinstance(v, str):
            errors.append(f"{card_id}.{field}: не строка")
            continue
        L = len(v.strip())
        if not (lo <= L <= hi):
            errors.append(f"{card_id}.{field}: {L} симв, нужно {lo}-{hi}")

    # grade / code / verdict
    if card.get("grade") not in VALID_GRADES:
        errors.append(f"{card_id}.grade: {card.get('grade')!r}")
    if card.get("code") not in VALID_CODES:
        errors.append(f"{card_id}.code: {card.get('code')!r}")
    if card.get("verdict") not in VALID_VERDICTS:
        errors.append(f"{card_id}.verdict: {card.get('verdict')!r}")

    # effects
    effects = card.get("effects", [])
    if not isinstance(effects, list) or not (1 <= len(effects) <= 3):
        errors.append(f"{card_id}.effects: нужно 1-3, есть {len(effects) if isinstance(effects, list) else '?'}")
    else:
        for i, ef in enumerate(effects):
            if not isinstance(ef, str) or not (5 <= len(ef) <= 40):
                errors.append(f"{card_id}.effects[{i}]: {len(ef) if isinstance(ef, str) else '?'} симв (5-40)")

    # mechs
    mechs = card.get("mechs", [])
    if not isinstance(mechs, list) or not (2 <= len(mechs) <= 4):
        errors.append(f"{card_id}.mechs: нужно 2-4, есть {len(mechs) if isinstance(mechs, list) else '?'}")
    else:
        for i, m in enumerate(mechs):
            if not isinstance(m, list) or len(m) != 3:
                errors.append(f"{card_id}.mechs[{i}]: не [механизм, эффект, сила]")
                continue
            mech, eff, strength = m
            if not isinstance(mech, str) or not (20 <= len(mech) <= 250):
                errors.append(f"{card_id}.mechs[{i}].механизм: {len(mech) if isinstance(mech, str) else '?'} (20-250)")
            if not isinstance(eff, str) or not (5 <= len(eff) <= 120):
                errors.append(f"{card_id}.mechs[{i}].эффект: {len(eff) if isinstance(eff, str) else '?'} (5-120)")
            if strength not in VALID_STRENGTH:
                errors.append(f"{card_id}.mechs[{i}].сила: {strength!r}")

    # key_sources: 1-3 (1 допустимо если данных мало — грейд C/D)
    ks = card.get("key_sources", [])
    if not isinstance(ks, list) or not (1 <= len(ks) <= 3):
        errors.append(f"{card_id}.key_sources: нужно 1-3, есть {len(ks) if isinstance(ks, list) else '?'}")
    elif len(ks) == 1 and card.get("grade") not in ("C", "D"):
        errors.append(f"{card_id}.key_sources: 1 источник только для грейда C/D (сейчас {card.get('grade')})")
    else:
        for i, s in enumerate(ks):
            if not isinstance(s, dict):
                errors.append(f"{card_id}.key_sources[{i}]: не dict")
                continue
            if not s.get("pmid"):
                errors.append(f"{card_id}.key_sources[{i}]: пустой pmid")
            if not isinstance(s.get("year"), int):
                errors.append(f"{card_id}.key_sources[{i}].year: не int ({s.get('year')!r})")
            if not s.get("journal"):
                errors.append(f"{card_id}.key_sources[{i}]: пустой journal")

    # interactions
    inter = card.get("interactions", [])
    if not isinstance(inter, list) or not inter:
        errors.append(f"{card_id}.interactions: пусто")
    else:
        for i, it in enumerate(inter):
            if not isinstance(it, dict):
                errors.append(f"{card_id}.interactions[{i}]: не dict")
                continue
            if not it.get("with"):
                errors.append(f"{card_id}.interactions[{i}]: нет with")
            if it.get("severity") not in ("low", "medium", "high", "critical"):
                errors.append(f"{card_id}.interactions[{i}].severity: {it.get('severity')!r}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", required=True, type=str)
    args = ap.parse_args()

    path = PROPOSAL_DIR / args.proposal
    if not path.exists():
        print(f"[ERROR] Не найден: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"Proposal: {args.proposal}")
    print(f"Карточек: {len(data)}\n")

    total_errors = 0
    for card_id, card in data.items():
        errs = validate_card(card_id, card)
        if errs:
            print(f"❌ {card_id}:")
            for e in errs:
                print(f"   {e}")
            total_errors += len(errs)
        else:
            print(f"✅ {card_id}")

    print()
    if total_errors:
        print(f"[FAIL] {total_errors} ошибок")
        return 1
    print("[OK] 0 ошибок")
    return 0


if __name__ == "__main__":
    sys.exit(main())