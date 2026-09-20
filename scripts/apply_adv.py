"""Применяет adv-поля (Q1.4) к data.json.

Читает proposal JSON, валидирует длины, пишет в docs/data.json.

Использование:
    python scripts/apply_adv.py --proposal q14_batch_1_proposal.json
    python scripts/apply_adv.py --proposal q14_batch_1_proposal.json --apply
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
PROPOSAL_DIR = ROOT / "reports"

ADV_FIELDS = ["about", "who_needs", "onset", "myths",
              "food_sources", "guidelines", "how_to_choose"]

# Валидные диапазоны (на основе 20 существующих, +/− 30% запас)
LIMITS = {
    "about":         (30, 160),
    "who_needs":     (40, 180),
    "onset":         (30, 150),
    "myths":         (60, 220),
    "food_sources":  (25, 180),
    "guidelines":    (40, 180),
    "how_to_choose": (35, 180),
}


def validate(card_id: str, field: str, value) -> None:
    if not isinstance(value, str):
        raise AssertionError(f"{card_id}.{field}: не строка ({type(value).__name__})")
    v = value.strip()
    if not v:
        raise AssertionError(f"{card_id}.{field}: пусто")
    lo, hi = LIMITS[field]
    if not (lo <= len(v) <= hi):
        raise AssertionError(
            f"{card_id}.{field}: {len(v)} симв, ожидаем {lo}-{hi} «{v[:60]}…»"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", required=True, help="имя JSON в reports/")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    proposal_path = PROPOSAL_DIR / args.proposal
    if not proposal_path.exists():
        print(f"[!] Нет файла: {proposal_path}")
        return 2

    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    print(f"Карточек в proposal: {len(proposal)}")
    print(f"Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    stats = {f: {"n": 0, "min": 9999, "max": 0} for f in ADV_FIELDS}

    for card_id, fields in proposal.items():
        card = next((c for c in data if c["id"] == card_id), None)
        if not card:
            print(f"[!] {card_id} не найдена")
            return 3

        # Валидация всех 7 полей
        for f in ADV_FIELDS:
            if f not in fields:
                print(f"[!] {card_id}: отсутствует поле {f}")
                return 4
            validate(card_id, f, fields[f])
            stats[f]["n"] += 1
            ln = len(fields[f])
            stats[f]["min"] = min(stats[f]["min"], ln)
            stats[f]["max"] = max(stats[f]["max"], ln)

        if args.apply:
            for f in ADV_FIELDS:
                card[f] = fields[f].strip()

        print(f"✓ {card_id}  ({len(fields['about'])}/{len(fields['who_needs'])}/... симв)")

    print(f"\n{'='*60}")
    print("Статистика длин:")
    for f in ADV_FIELDS:
        s = stats[f]
        print(f"  {f:20s}  n={s['n']}  min={s['min']:3d}  max={s['max']:3d}")

    if args.apply:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = DATA_JSON.with_suffix(f".json.bak-{ts}")
        shutil.copy2(DATA_JSON, backup)
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n[OK] Бэкап: {backup.name}")
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print(f"\n[dry-run] данные не записаны.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())