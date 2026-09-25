"""Ревью evidence-файлов: что нашли, релевантно ли, свежее ли.

Показывает по каждой добавке: PMID, год, журнал, заголовок первого MA.
Быстрая проверка глазами — относится ли к веществу.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports" / "evidence"
DRAFTS = ROOT / "docs" / "_drafts.json"


def parse_md(path: Path) -> list[dict]:
    """Извлекает из evidence-файла список PMID + заголовков."""
    text = path.read_text(encoding="utf-8")
    # Паттерн: ### PMID [12345678](https://pubmed...)
    # **Title** — _Journal, Year_
    items = []
    for m in re.finditer(
        r"###\s+PMID\s+\[(\d+)\].*?\n\*\*(.+?)\*\*\s+—\s+_(.+?),\s+(\d{4})_",
        text, re.DOTALL,
    ):
        items.append({
            "pmid": m.group(1),
            "title": m.group(2).strip()[:120],
            "journal": m.group(3).strip(),
            "year": m.group(4),
        })
    return items


def main() -> int:
    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
    draft_ids = [c["id"] for c in drafts]

    print("=" * 100)
    print(f"  РЕВЬЮ EVIDENCE — {len(draft_ids)} карточек")
    print("=" * 100)
    print()

    stats = {
        "total": 0,
        "no_ma": 0,       # нет ни одного MA
        "old_ma": 0,      # все MA старше 2019
        "thin_ma": 0,     # меньше 3 MA
    }

    for cid in draft_ids:
        path = EVIDENCE / f"{cid}.md"
        if not path.exists():
            print(f"❌ {cid}: нет evidence-файла")
            continue

        items = parse_md(path)
        stats["total"] += 1

        # Флаги
        if not items:
            flag = "🔴 НЕТ MA"
            stats["no_ma"] += 1
        else:
            years = [int(i["year"]) for i in items]
            if max(years) < 2019:
                flag = "🟡 СТАРЫЕ"
                stats["old_ma"] += 1
            elif len(items) < 3:
                flag = f"🟡 ТОЛЬКО {len(items)}"
                stats["thin_ma"] += 1
            else:
                flag = "✅"

        print(f"{flag} {cid}")
        for i, item in enumerate(items, 1):
            title = item["title"]
            print(f"   [{i}] PMID {item['pmid']} ({item['year']}, {item['journal'][:30]})")
            print(f"       {title}")
        print()

    # Сводка
    print("=" * 100)
    print("  СВОДКА")
    print("=" * 100)
    print(f"  Всего: {stats['total']}")
    print(f"  🔴 Нет MA вообще:        {stats['no_ma']}")
    print(f"  🟡 Все MA старше 2019:   {stats['old_ma']}")
    print(f"  🟡 Меньше 3 MA:          {stats['thin_ma']}")
    print(f"  ✅ Всё ок:               {stats['total'] - stats['no_ma'] - stats['old_ma'] - stats['thin_ma']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())