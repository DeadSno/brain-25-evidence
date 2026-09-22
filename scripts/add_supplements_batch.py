"""Batch-добавление добавок из CSV.

Читает CSV, создаёт:
  - записи в src/config.py → SUPPLEMENTS
  - записи в docs/data_pubmed_terms.json
  - черновики карточек в docs/_drafts.json (data.json не трогается)

После ручного заполнения → scripts/apply_drafts.py

CSV-формат (заголовки обязательны):
  name,term,category,query,code
  Шатавари,Asparagus racemosus,Общее,(Asparagus racemosus) AND (hormone OR menopause),0

Использование:
    python scripts\\add_supplements_batch.py --input scripts\\supplements_to_add.csv
    python scripts\\add_supplements_batch.py --input scripts\\supplements_to_add.csv --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "src" / "config.py"
TERMS = ROOT / "docs" / "data_pubmed_terms.json"
DATA = ROOT / "docs" / "data.json"
DRAFTS = ROOT / "docs" / "_drafts.json"

CATEGORIES = {
    "Когниция", "Сон", "Спорт", "Иммунитет", "Настроение",
    "Кожа и суставы", "Кишечник", "Общее", "Метаболизм",
    "Сердце/сосуды", "Кости/Иммунитет", "Гормоны",
    "Неврология/Метаболизм", "Антиоксидант/Неврология",
}

FILLED_FIELDS = [
    "verdict", "dosage", "course", "caution", "about", "who_needs",
    "onset", "upper_limit", "food_sources", "guidelines",
    "how_to_choose", "myths",
]


def load_existing_cards() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def card_template(name: str, category: str, code: int) -> dict:
    """Заготовка на основе структуры Креатина."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "id": name,
        "name": name,
        "code": code,
        "verdict": "_пусто_",
        "category": category,
        "scienceIndex": None,
        "metaCount": None,
        "citations": None,
        "wiki": None,
        "ongoing": None,
        "effects": [],
        "dosage": "_пусто_",
        "course": "_пусто_",
        "caution": "_пусто_",
        "forms": None,
        "mechs": [],
        "interactions": [],
        "about": "_пусто_",
        "who_needs": "_пусто_",
        "onset": "_пусто_",
        "upper_limit": "_пусто_",
        "food_sources": "_пусто_",
        "guidelines": "_пусто_",
        "how_to_choose": "_пусто_",
        "myths": "_пусто_",
        "hedges_g": None,
        "grade": "_пусто_",
        "key_sources": [],
        "updated": today,
    }


def check_config_has(name: str, text: str) -> bool:
    return f'"{name}"' in text


def add_to_config(text: str, name: str, term: str) -> tuple[str, bool]:
    """Вставить новую запись ПЕРЕД закрывающей } у SUPPLEMENTS."""
    m = re.search(r'(SUPPLEMENTS\s*=\s*\{)(.*?)(\n\})', text, re.DOTALL)
    if not m:
        return text, False

    body = m.group(2).rstrip()
    pad = max(1, 28 - len(name))
    new_line = f'\n    "{name}":{" " * pad}"{term}",'

    # Собираем: { + body + new_line + \n} + остальное
    return text[:m.end(1)] + body + new_line + text[m.start(3):], True


def read_csv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue
            rows.append({
                "name": name,
                "term": (row.get("term") or "").strip(),
                "category": (row.get("category") or "Общее").strip(),
                "query": (row.get("query") or "").strip(),
                "code": int(row.get("code") or 0),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch-добавление добавок")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"[ERROR] CSV не найден: {args.input}", file=sys.stderr)
        return 1

    rows = read_csv(args.input)
    if not rows:
        print("[ERROR] CSV пуст", file=sys.stderr)
        return 1

    existing = load_existing_cards()
    existing_ids = {c["id"] for c in existing}
    config_text = CONFIG.read_text(encoding="utf-8")
    terms = json.loads(TERMS.read_text(encoding="utf-8"))
    drafts = json.loads(DRAFTS.read_text(encoding="utf-8")) if DRAFTS.exists() else []

    to_add: list[dict] = []
    skipped: list[tuple[str, str]] = []

    for r in rows:
        name = r["name"]
        if r["category"] not in CATEGORIES:
            skipped.append((name, f"категория '{r['category']}' не из списка"))
            continue
        if name in existing_ids:
            skipped.append((name, "уже в data.json"))
            continue
        if check_config_has(name, config_text):
            skipped.append((name, "уже в config.py"))
            continue
        if any(d["id"] == name for d in drafts):
            skipped.append((name, "уже в _drafts.json"))
            continue
        if not r["query"]:
            r["query"] = f"({r['term']})"
        to_add.append(r)

    print(f"К добавлению: {len(to_add)}")
    print(f"Пропущено:    {len(skipped)}")
    for name, reason in skipped:
        print(f"  [SKIP] {name}: {reason}")
    print()

    if not to_add:
        print("Нечего добавлять.")
        return 0

    if args.dry_run:
        for r in to_add:
            print(f"  + {r['name']:20} {r['category']:20} {r['query'][:60]}")
        print("\n[DRY-RUN] Файлы не изменены.")
        return 0

    # Бэкапы
    for p in [CONFIG, TERMS]:
        shutil.copy(p, str(p) + ".bak")

    # config.py
    added_config = 0
    for r in to_add:
        config_text, ok = add_to_config(config_text, r["name"], r["term"])
        if not ok:
            print(f"[WARN] config.py: не удалось добавить {r['name']}", file=sys.stderr)
        else:
            added_config += 1
    CONFIG.write_text(config_text, encoding="utf-8")
    print(f"[OK] config.py → +{added_config} записей")

    if added_config != len(to_add):
        print(f"[ERROR] config.py: добавлено {added_config} из {len(to_add)}, откатывай .bak",
              file=sys.stderr)
        return 1

    # data_pubmed_terms.json
    for r in to_add:
        terms[r["name"]] = r["query"]
    TERMS.write_text(
        json.dumps(terms, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] data_pubmed_terms.json → +{len(to_add)} записей")

    # _drafts.json
    for r in to_add:
        drafts.append(card_template(r["name"], r["category"], r["code"]))
    DRAFTS.write_text(
        json.dumps(drafts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] _drafts.json → {len(drafts)} черновиков")

    print()
    print("=" * 62)
    print(f"ДАЛЬШЕ:")
    print("=" * 62)
    print(f"  1. Заполни docs/_drafts.json ({len(to_add)} карточек)")
    print(f"  2. python scripts\\apply_drafts.py")
    print(f"  3. python scripts\\update_all.py --apply")
    print(f"  4. python scripts\\build_index.py")
    print(f"  5. python -m pytest -q -m 'not network'")
    print()
    print(f"Откатить config.py / data_pubmed_terms.json: переименуй .bak обратно")
    return 0


if __name__ == "__main__":
    sys.exit(main())