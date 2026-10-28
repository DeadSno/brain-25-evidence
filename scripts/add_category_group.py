#!/usr/bin/env python3
"""
Миграция: добавляет структурное поле category_group ко всем карточкам
в data.json (RU) и data_en.json (EN).

Вместо хрупкого поиска русских подстрок в CAT_GROUPS (docs/script.js:971-987)
каждая карточка получает category_group — одно из 12 значений:
brain, metab, bone, cardio, immune, sport, gut, general, liver, vision, women, critical.

Логика определения группы повторяет существующий catGroup():
  - берет первый сегмент категории (до '/', ' и ', ',')
  - ищет совпадение по ключевым словам (русские для RU, английские для EN)
  - fallback: ищет по всей строке
  - если не найдено → 'neutral'

Запуск: python scripts/add_category_group.py
"""

import json
import re
import sys

DATA_RU = "docs/data.json"
DATA_EN = "docs/data_en.json"

# Английский эквивалент CAT_GROUPS (подстроки на EN, порядок как в RU-оригинале)
CAT_GROUPS_EN = [
    ("gut", ["gi", "digest", "stomach", "intestinal", "gut"]),
    ("cardio", ["heart", "vessel", "blood", "kidney", "urogen", "vein", "pressure"]),
    ("bone", ["bone", "joint", "mineral", "skin", "osteo"]),
    ("liver", ["liver"]),
    ("brain", ["brain", "cogn", "neurolog", "nerv", "psych", "sleep", "mood", "stress", "adaptogen", "memor", "dement", "mental", "depress"]),
    ("immune", ["immune", "immunity", "ori", "antioxid", "inflamm", "mushroom", "flu"]),
    ("metab", ["metabol", "hormon", "energ", "sexual", "perform", "diabet", "cholesterol", "weight", "insulin"]),
    ("sport", ["sport", "muscle", "endur", "vigor"]),
    ("women", ["pregnan", "women", "pcos", "children"]),
    ("vision", ["vision", "eye", "retin", "visual"]),
    ("general", ["general", "aging", "longev", "geriatr"]),
    ("critical", ["critical", "resusc", "intensiv"]),
]

VALID_GROUPS = {g for g, _ in CAT_GROUPS_EN} | {"neutral"}


def cat_group(raw, groups):
    """Повторяет логику catGroup() из docs/script.js."""
    s = str(raw or "").lower()
    head = re.split(r"[/,]|[ ]и[ ]", s)[0].strip()
    for g, keys in groups:
        if any(k in head for k in keys):
            return g
    for g, keys in groups:
        if any(k in s for k in keys):
            return g
    return "neutral"


def main():
    # ---------- RU: data.json ----------
    with open(DATA_RU, encoding="utf-8") as f:
        ru = json.load(f)

    ru_groups = [
        ("gut", ["жкт", "кишечник", "пищевар"]),
        ("cardio", ["сердце", "сосуд", "кров", "почки", "мочеполов", "мочевывод", "вены", "давлен"]),
        ("bone", ["кост", "сустав", "минерал", "кожа", "остео"]),
        ("liver", ["печень"]),
        ("brain", ["мозг", "когни", "невролог", "нервн", "психи", "сон", "настроен", "стресс", "усталость", "адаптоген", "памят", "деменц"]),
        ("immune", ["иммунитет", "орви", "антиоксид", "воспален", "грибы", "грипп"]),
        ("metab", ["метабол", "гормон", "энерг", "сексуальн", "производительн", "диабет", "холестерин", "вес", "инсулин"]),
        ("sport", ["спорт", "мышц", "выносл", "бодрость"]),
        ("women", ["беременн", "женск", "спкя", "дети"]),
        ("vision", ["зрени", "глаза", "сетчат", "зрительн"]),
        ("general", ["общее", "старени", "долголет", "гериатр"]),
        ("critical", ["критическ", "реанимац", "интенсив"]),
    ]

    ru_cat_groups = {}
    ru_neutral = []
    for card in ru:
        cat = card.get("category", "")
        g = cat_group(cat, ru_groups)
        card["category_group"] = g
        ru_cat_groups[cat] = g
        if g == "neutral":
            ru_neutral.append((card.get("id"), cat))

    with open(DATA_RU, "w", encoding="utf-8") as f:
        json.dump(ru, f, ensure_ascii=False, indent=2)

    # ---------- EN: data_en.json ----------
    with open(DATA_EN, encoding="utf-8") as f:
        en = json.load(f)

    supplements = en["supplements"]
    en_cat_groups = {}
    en_neutral = []
    for key, card in supplements.items():
        cat = card.get("category", "")
        g = cat_group(cat, CAT_GROUPS_EN)
        card["category_group"] = g
        en_cat_groups[cat] = g
        if g == "neutral":
            en_neutral.append((key, cat))

    with open(DATA_EN, "w", encoding="utf-8") as f:
        json.dump(en, f, ensure_ascii=False, indent=2)

    # ---------- Отчёт ----------
    print("=== RU (data.json) ===")
    print(f"Карточек: {len(ru)}")
    print(f"category_group добавлен: {sum(1 for c in ru if 'category_group' in c)}")
    print(f"neutral: {len(ru_neutral)}")
    for _id, cat in ru_neutral:
        print(f"  NEUTRAL: id={_id!r} category={cat!r}")
    print("\nРаспределение по группам (RU):")
    from collections import Counter
    cnt = Counter(c["category_group"] for c in ru)
    for g, n in sorted(cnt.items()):
        print(f"  {g:10s}: {n}")

    print("\n=== EN (data_en.json) ===")
    print(f"Карточек: {len(supplements)}")
    print(f"category_group добавлен: {sum(1 for c in supplements.values() if 'category_group' in c)}")
    print(f"neutral: {len(en_neutral)}")
    for key, cat in en_neutral:
        print(f"  NEUTRAL: key={key!r} category={cat!r}")
    print("\nРаспределение по группам (EN):")
    cnt = Counter(c["category_group"] for c in supplements.values())
    for g, n in sorted(cnt.items()):
        print(f"  {g:10s}: {n}")

    # ---------- Проверка ----------
    ru_cats_with_group = {c["category"] for c in ru if c.get("category_group") != "neutral"}
    en_cats_with_group = {c["category"] for c in supplements.values() if c.get("category_group") != "neutral"}
    ru_neutral_cats = {c["category"] for c in ru if c.get("category_group") == "neutral"}
    en_neutral_cats = {c["category"] for c in supplements.values() if c.get("category_group") == "neutral"}

    print("\n=== Проверка согласованности RU/EN ===")
    print(f"RU категории с группой: {len(ru_cats_with_group)}, neutral: {len(ru_neutral_cats)}")
    print(f"EN категории с группой: {len(en_cats_with_group)}, neutral: {len(en_neutral_cats)}")

    all_ru_have_group = all("category_group" in c and c["category_group"] in VALID_GROUPS for c in ru)
    all_en_have_group = all("category_group" in c and c["category_group"] in VALID_GROUPS for c in supplements.values())
    print(f"Все RU карточки имеют валидный category_group: {all_ru_have_group}")
    print(f"Все EN карточки имеют валидный category_group: {all_en_have_group}")

    if ru_neutral or en_neutral:
        print("\nWARNING: cards with neutral remain - manual review required!")
        sys.exit(1)
    print("\nOK: all cards have category_group from 12 valid values.")


if __name__ == "__main__":
    main()
