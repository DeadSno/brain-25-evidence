"""Собирает docs/effect_tags.json из scripts/effect_tags_map.py.

роверяет, что все id из TAGS есть в data.json и наоборот.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.effect_tags_map import TAG_LABELS, TAGS  # noqa: E402

DATA = json.loads((ROOT / "docs/data.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "effect_tags.json"


def main() -> int:
    ids_data = {c["id"] for c in DATA}
    ids_tags = set(TAGS.keys())

    missing_in_tags = ids_data - ids_tags
    missing_in_data = ids_tags - ids_data

    if missing_in_tags:
        print(f"[!] нет в TAGS ({len(missing_in_tags)}): {sorted(missing_in_tags)}")
    if missing_in_data:
        print(f"[!] нет в data.json ({len(missing_in_data)}): {sorted(missing_in_data)}")
    if missing_in_tags or missing_in_data:
        return 1

    # алидация: все теги — из TAG_LABELS, без дублей
    for cid, tags in TAGS.items():
        for t in tags:
            if t not in TAG_LABELS:
                print(f"[!] {cid}: неизвестный тег {t!r}")
                return 1
        if len(tags) != len(set(tags)):
            print(f"[!] {cid}: дубли тегов {tags}")
            return 1

    # Сортируем ключи для стабильного diff
    ordered = {k: TAGS[k] for k in sorted(TAGS.keys())}
    OUT.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] аписано: {OUT}")

    # аспределение
    counts = Counter(t for tags in TAGS.values() for t in tags)
    print(f"\n=== аспределение ({len(counts)} тегов) ===")
    for tag, _ in sorted(TAG_LABELS.items(), key=lambda x: -counts.get(x[0], 0)):
        n = counts.get(tag, 0)
        bar = "█" * n
        print(f"  {TAG_LABELS[tag]:22s} {n:2d}  {bar}")

    # роверка, что все теги из TAG_LABELS где-то используются
    unused = [t for t in TAG_LABELS if t not in counts]
    if unused:
        print(f"\n[i] е используются ни в одной карточке: {unused}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
