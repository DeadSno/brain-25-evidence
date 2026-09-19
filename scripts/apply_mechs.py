"""Применяет proposal mechs к data.json.

Читает JSON-файл из reports/ (по умолчанию mechs_pilot_proposal.json),
валидирует, пишет в docs/data.json.

Использование:
    python scripts/apply_mechs.py                                  # dry-run
    python scripts/apply_mechs.py --apply                          # записать
    python scripts/apply_mechs.py --proposal mechs_batch_1_proposal.json --apply
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
PROPOSAL_DIR = ROOT / "reports"

VALID_STRENGTH = {"сильно", "умеренно", "слабо", "контекст", "маркетинг"}


def validate_mech(mech: list, card_id: str, idx: int) -> None:
    assert isinstance(mech, list), f"{card_id}[{idx}]: не список"
    assert len(mech) == 3, f"{card_id}[{idx}]: должно быть 3 поля, получено {len(mech)}"
    m, eff, strength = mech
    assert isinstance(m, str) and 20 <= len(m) <= 250, (
        f"{card_id}[{idx}]: механизм {len(m)} симв, нужно 20-250"
    )
    assert isinstance(eff, str) and 5 <= len(eff) <= 120, (
        f"{card_id}[{idx}]: эффект {len(eff)} симв, нужно 5-120"
    )
    assert strength in VALID_STRENGTH, (
        f"{card_id}[{idx}]: сила {strength!r} не из {VALID_STRENGTH}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--proposal", default="mechs_pilot_proposal.json",
                    help="имя JSON-файла в reports/")
    args = ap.parse_args()

    proposal_path = PROPOSAL_DIR / args.proposal
    if not proposal_path.exists():
        print(f"[!] Нет файла: {proposal_path}")
        print(f"    Сначала запусти big pickle с брифом (--proposal {args.proposal})")
        return 2

    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    print(f"Карточек в proposal: {len(proposal)}")
    print(f"Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    for card_id, mechs in proposal.items():
        card = next((c for c in data if c["id"] == card_id), None)
        if not card:
            print(f"[!] Карточка не найдена: {card_id}")
            return 3

        for idx, mech in enumerate(mechs):
            validate_mech(mech, card_id, idx)

        old_count = len(card.get("mechs") or [])
        new_count = len(mechs)
        print(f"{card_id:25s} | mechs: {old_count} → {new_count}")

        for idx, (m, eff, strength) in enumerate(mechs, 1):
            print(f"  {idx}. [{strength:10s}] {m[:70]}...")

        if args.apply:
            card["mechs"] = mechs

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
        print("\n[dry-run] данные не записаны. Добавьте --apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())