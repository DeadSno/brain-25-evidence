"""Генерация docs/data_index.json — лёгкая проекция data.json.

Зачем: главная и калькулятор грузят 472 KB ради карточек.
Индекс — ~50 KB, те же карточки. Полный data.json — по требованию
при открытии модалки (кешируется).

Поля согласованы с index.html + calculator.html.
Snapshot-тест: tests/test_index_sync.py

Запуск:
    python scripts/build_index.py            # только собрать
    python scripts/build_index.py --check    # проверка синхронизации (для CI)

Если data.json обновился (update_all.py), пересобрать:
    python scripts/build_index.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
INDEX = ROOT / "docs" / "data_index.json"

# Поля, нужные для карточек/фильтров/калькулятора (без модалки)
INDEX_FIELDS = [
    "id", "name", "category", "code", "verdict", "grade",
    "scienceIndex", "metaCount", "citations", "wiki", "ongoing",
    "effects", "updated", "interactions", "upper_limit", "hedges_g",
    "price",                        # future-proof (сейчас 0/81, но дешёв)
    "synergists", "antagonists",    # для fav banner (checkInteractions)
]


def build_projection(rows: list[dict]) -> list[dict]:
    out = []
    for c in rows:
        item = {k: c[k] for k in INDEX_FIELDS if k in c}
        out.append(item)
    return out


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def cmd_build() -> int:
    if not DATA.exists():
        print(f"[ERROR] {DATA} не найден", file=sys.stderr)
        return 1

    full = json.loads(DATA.read_text(encoding="utf-8"))
    index = build_projection(full)

    payload = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "data.json",
            "source_sha256_16": sha256_of(DATA.read_text(encoding="utf-8")),
            "fields": INDEX_FIELDS,
            "count": len(index),
        },
        "supplements": index,
    }

    INDEX.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    full_size = DATA.stat().st_size
    idx_size = INDEX.stat().st_size
    ratio = idx_size / full_size * 100

    print(f"[OK] {INDEX}")
    print(f"     карточек: {len(index)}")
    print(f"     размер:   {idx_size:,} байт ({idx_size/1024:.1f} KB)")
    print(f"     было:     {full_size:,} байт ({full_size/1024:.1f} KB)")
    print(f"     сжатие:   {ratio:.1f}%")
    return 0


def cmd_check() -> int:
    """Для CI: убедиться, что data_index.json синхронизирован с data.json."""
    if not INDEX.exists():
        print(f"[FAIL] {INDEX} не существует. Запусти: python scripts/build_index.py", file=sys.stderr)
        return 1

    full = json.loads(DATA.read_text(encoding="utf-8"))
    expected = build_projection(full)

    payload = json.loads(INDEX.read_text(encoding="utf-8"))
    actual = payload.get("supplements", [])

    if expected != actual:
        print("[FAIL] data_index.json не синхронизирован с data.json", file=sys.stderr)
        print(f"       ожидалось карточек: {len(expected)}, в индексе: {len(actual)}", file=sys.stderr)
        # Показать первую разницу
        for i, (e, a) in enumerate(zip(expected, actual)):
            if e != a:
                print(f"       первая разница в позиции {i}: id={e.get('id')}", file=sys.stderr)
                break
        return 1

    print(f"[OK] data_index.json синхронизирован ({len(actual)} карточек)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Генерация/проверка data_index.json")
    ap.add_argument("--check", action="store_true",
                    help="только проверить синхронизацию (для CI)")
    args = ap.parse_args()
    return cmd_check() if args.check else cmd_build()


if __name__ == "__main__":
    sys.exit(main())