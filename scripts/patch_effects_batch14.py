"""Одноразовый патч: добавляет effects в q14_batch_14_proposal.json.

Effects — короткие названия исходов (как "Рабочая память под нагрузкой"
у Креатина). Выведены из mechs вручную.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "reports" / "q14_batch_14_proposal.json"

EFFECTS = {
    "B1": [
        "Нейропатия",
        "Алкогольная нейропатия",
    ],
    "Холин": [
        "Когниция",
        "Нервная трубка плода",
        "Функция и поведение",
    ],
    "EPA": [
        "Депрессия",
        "Триглицериды",
        "Кардиориск",
    ],
}


def main() -> int:
    if not PROPOSAL.exists():
        print(f"[ERROR] Нет файла: {PROPOSAL}", file=sys.stderr)
        return 1

    data = json.loads(PROPOSAL.read_text(encoding="utf-8"))

    bak = PROPOSAL.with_suffix(".json.bak")
    shutil.copy(PROPOSAL, bak)
    print(f"[OK] Backup: {bak}")

    for name, effects in EFFECTS.items():
        if name not in data:
            print(f"[WARN] {name} нет в proposal")
            continue
        data[name]["effects"] = effects
        print(f"  {name}: +{len(effects)} effects")

    PROPOSAL.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n[OK] {PROPOSAL} обновлён")
    return 0


if __name__ == "__main__":
    sys.exit(main())