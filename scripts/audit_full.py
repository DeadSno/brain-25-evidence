"""Полный аудит: заполненность карточек + отображение на страницах.

Запуск:  python scripts/audit_full.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    # === Данные ===
    data = load(ROOT / "docs" / "data.json")
    tags = load(ROOT / "docs" / "effect_tags.json")
    dosage = load(ROOT / "docs" / "dosage_parsed.json")
    ts = load(ROOT / "docs" / "timeseries.json")
    papers_slim = load(ROOT / "data" / "papers" / "papers_slim.json")

    cards = data if isinstance(data, list) else list(data.values())
    total = len(cards)

    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  АУДИТ brain-25-evidence                     ║")
    print(f"║  Всего карточек: {total:<28} ║")
    print(f"╚══════════════════════════════════════════════╝\n")

    # === 1. Поля: заполненность ===
    print("=" * 60)
    print("  1. ЗАПОЛНЕННОСТЬ ПОЛЕЙ")
    print("=" * 60)

    FIELDS = [
        # базовые
        ("verdict",        "вердикт"),
        ("grade",          "грейд"),
        ("category",       "категория"),
        ("scienceIndex",   "индекс науки"),
        ("metaCount",      "мета-анализы"),
        ("rct",            "РКИ"),
        ("citations",      "цитаты"),
        ("wiki",           "wiki-просмотры"),
        ("ongoing",        "активных испытаний"),
        # контент
        ("effects",        "эффекты"),
        ("mechs",          "механизмы"),
        ("interactions",   "взаимодействия"),
        ("dosage",         "дозировка"),
        ("course",         "курс"),
        ("caution",        "предостережения"),
        ("upper_limit",    "верхний предел"),
        # adv
        ("about",          "about"),
        ("who_needs",      "who_needs"),
        ("onset",          "onset"),
        ("myths",          "myths"),
        ("food_sources",   "food_sources"),
        ("guidelines",     "guidelines"),
        ("how_to_choose",  "how_to_choose"),
        # доказательства
        ("hedges_g",       "Hedges' g"),
        ("hedges_g_ci",    "Hedges' g CI"),
        ("key_sources",    "key_sources"),
        ("ma_top3",        "top-3 MA"),
        ("pubmed_term",    "PubMed-запрос"),
    ]

    for field, label in FIELDS:
        filled = 0
        for c in cards:
            v = c.get(field)
            if v is None: continue
            if isinstance(v, str) and not v.strip(): continue
            if isinstance(v, (list, dict)) and len(v) == 0: continue
            filled += 1
        pct = filled / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        flag = "✅" if pct >= 95 else ("⚠️" if pct >= 60 else "❌")
        print(f"  {flag} {label:<20} {filled:>3}/{total}  {bar} {pct:>5.1f}%")

    # === 2. Покрытие по страницам ===
    print()
    print("=" * 60)
    print("  2. ОТОБРАЖЕНИЕ НА СТРАНИЦАХ")
    print("=" * 60)

    # Index (главная): все карточки
    print(f"  📊 index.html — все карточки: {total}")

    # Map (карта механизмов): только с mechs
    with_mechs = sum(1 for c in cards if c.get("mechs"))
    print(f"  🧩 map.html — карточки с mechs: {with_mechs}/{total}")

    # Atlas (атлас): только с effect_tags
    with_tags = sum(1 for c in cards if c["id"] in tags)
    print(f"  🌐 atlas.html — с effect_tags: {with_tags}/{total}")

    # Calculator: только с dosage_parsed
    with_dosage = sum(1 for c in cards if c["id"] in dosage)
    print(f"  🧮 calculator.html — с dosage_parsed: {with_dosage}/{total}")

    # Interactions: с interactions
    with_inter = sum(1 for c in cards if c.get("interactions"))
    print(f"  🔗 interactions.html — с interactions: {with_inter}/{total}")

    # Trends: с временными рядами
    ts_pubmed = len(ts.get("pubmed", {}))
    ts_wiki = len(ts.get("wiki", {}))
    ts_cit = len(ts.get("citations", {}))
    print(f"  📈 trends.html — с pubmed TS: {ts_pubmed}/{total}, с wiki TS: {ts_wiki}, с citations TS: {ts_cit}")

    # Streamlit: с papers_slim
    print(f"  🧠 streamlit — papers_slim: {len(papers_slim)} записей")

    # === 3. Что НЕ отображается ===
    print()
    print("=" * 60)
    print("  3. КАРТОЧКИ БЕЗ ПОЛЕЙ — список")
    print("=" * 60)

    CHECKS = [
        ("mechs",       "нет mechs → не в map.html"),
        ("effect_tags", "нет в effect_tags → не в atlas.html"),
        ("dosage",      "нет в dosage_parsed → fallback в calculator"),
        ("hedges_g",    "нет Hedges' g → не в scatter"),
        ("key_sources", "нет key_sources → нет источников"),
        ("about",       "нет about → пустая карточка"),
    ]

    for field, desc in CHECKS:
        missing = []
        for c in cards:
            if field == "effect_tags":
                if c["id"] not in tags:
                    missing.append(c["id"])
            elif field == "dosage":
                if c["id"] not in dosage:
                    missing.append(c["id"])
            else:
                v = c.get(field)
                if v is None or (isinstance(v, (list, str)) and len(v) == 0):
                    missing.append(c["id"])

        if missing:
            print(f"\n  ❌ {desc} — {len(missing)} шт:")
            for name in missing[:20]:
                print(f"      • {name}")
            if len(missing) > 20:
                print(f"      ... и ещё {len(missing) - 20}")
        else:
            print(f"\n  ✅ {desc} — все есть")

    # === 4. Грейды — распределение ===
    print()
    print("=" * 60)
    print("  4. РАСПРЕДЕЛЕНИЕ ГРЕЙДОВ")
    print("=" * 60)

    grades = Counter(c.get("grade", "—") for c in cards)
    for g in ["A", "B", "C", "D", "—"]:
        n = grades.get(g, 0)
        if n:
            pct = n / total * 100
            print(f"  {g}: {n:>3} ({pct:.1f}%)")

    # === 5. Категории ===
    print()
    print("=" * 60)
    print("  5. КАТЕГОРИИ")
    print("=" * 60)

    cats = Counter()
    for c in cards:
        for part in str(c.get("category", "")).split("/"):
            part = part.strip()
            if part:
                cats[part] += 1

    for cat, n in cats.most_common(20):
        print(f"  {cat:<35} {n}")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())