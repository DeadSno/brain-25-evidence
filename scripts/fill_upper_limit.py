"""Заполняет пустые upper_limit у 61 карточки.

Для витаминов/минералов — реальные UL (Institute of Medicine / EFSA).
Для трав/аминокислот — «Формального UL не установлен».

Источники UL:
- Institute of Medicine (IOM) Dietary Reference Intakes
- EFSA Tolerable Upper Intake Levels
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

NO_UL = "Формального UL не установлен — данных о токсичности нет."

# Известные UL (мг/сут, если не указано иное)
KNOWN_UL = {
    "B6":           "100 мг/сут (длительно >200 мг — нейротоксично)",
    "B9":           "1000 мкг/сут (синтетическая фолиевая кислота)",
    "Витамин E":    "1000 мг/сут (α-токоферол)",
    "Железо":       "45 мг/сут",
    "Кальций":      "2500 мг/сут",
    "Магний":       "350 мг/сут (из добавок; из еды — нет)",
    "Цинк":         "40 мг/сут",
    "Медь":         "10 мг/сут",
    "Селен":        "400 мкг/сут",
    "Витамин A":    "3000 мкг RAE/сут (преформированный)",
    "Витамин D":    "4000 МЕ/сут (без контроля врача)",
    "Йод":          "1100 мкг/сут",
    "Марганец":     "11 мг/сут",
    "Молибден":     "2000 мкг/сут",
    "Ниацин":       "35 мг/сут (никотиновая кислота)",
    "Холин":        "3500 мг/сут",
    "B3":           "35 мг/сут (никотиновая кислота)",
}


def main() -> int:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))

    changed = 0
    print(f"{'Карточка':<25} {'Новый UL':<60}")
    print("-" * 90)

    for c in data:
        v = c.get("upper_limit") or ""
        if v.strip():
            continue  # уже заполнено

        card_id = c["id"]
        new_ul = KNOWN_UL.get(card_id, NO_UL)
        print(f"{card_id:<25} {new_ul[:60]}")

        if args.apply:
            c["upper_limit"] = new_ul
        changed += 1

    print(f"\nВсего: {changed} карточек")

    if not args.apply:
        print("\n[DRY-RUN] Файл не изменён. Для записи: --apply")
        return 0

    bak = DATA.with_suffix(".json.bak")
    shutil.copy(DATA, bak)
    print(f"[OK] Бэкап: {bak.name}")

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"[OK] {DATA.name} обновлён")
    return 0


if __name__ == "__main__":
    sys.exit(main())