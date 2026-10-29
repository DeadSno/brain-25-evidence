"""Нормализация типов полей wiki/ongoing в данных (DATA-05, FIX-41).

Что не так
----------
`wiki` — просмотры ru.wikipedia за 12 месяцев, `ongoing` — число активных
исследований в ClinicalTrials.gov. Оба поля числовые, и канон для «данных
нет» в проекте — `null` (так помечены `hedges_g` и `hedges_g_ci`).
Исторически в 40 карточках `wiki` и в 36 карточках `ongoing` вместо `null`
лежала русская строка-заглушка «Нет данных». Потребители этого не ждут:

  docs/script.js:1147  s.wiki.toLocaleString(LOCALE)   — строка печаталась как число
  docs/script.js:1126  s.ongoing > 0                    — строка давала false
  docs/script.js:846   (s.ongoing || 0) >= 1            — то же
  docs/script.js:1411  a.ongoing ?? '—'                 — заглушка попадала в таблицу
  docs/trends.html:798 c.wiki.toLocaleString(LOCALE)    — то же

Почему миграция, а не правка генератора
---------------------------------------
Генератор `scripts/fetch_metrics.py` заглушку не пишет: он кладёт `int`
при успешном ответе API и не трогает поле при ошибке (строки 182-246).
То есть генератор уже соответствует канону, а расхождение накопилось в
самих данных до него. Перегенерация к нему не приведёт — она требует
сети (Wikimedia REST API, ClinicalTrials.gov), поэтому чинится разовой
миграцией, оформленной скриптом: её можно перезапускать и проверять в CI.

Тип: `int` или `null`. Ни float, ни bool, ни строк — «иногда строка»
не вариант: поле участвует в арифметике и в `toLocaleString`.

Запуск:
    python scripts/normalize_wiki_ongoing.py --check   # только проверка (CI)
    python scripts/normalize_wiki_ongoing.py           # переписать данные
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RU = ROOT / "docs" / "data.json"
DATA_EN = ROOT / "docs" / "data_en.json"

FIELDS = ("wiki", "ongoing")

#: Строковые заглушки, встречавшиеся в данных вместо null.
PLACEHOLDERS = frozenset({"Нет данных", "нет данных", "no data", "—", ""})


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ru_cards(data) -> list[dict]:
    """docs/data.json — плоский список карточек."""
    if isinstance(data, list):
        return data
    raise SystemExit(f"[FAIL] {DATA_RU}: ожидался список карточек, а не {type(data).__name__}")


def en_cards(data) -> list[dict]:
    """docs/data_en.json — оверлей {_meta, supplements: {id: {...}}}."""
    if isinstance(data, dict):
        return list((data.get("supplements") or {}).values())
    raise SystemExit(f"[FAIL] {DATA_EN}: ожидался объект с supplements, а не {type(data).__name__}")


def is_canonical(value) -> bool:
    """int (не bool) или None."""
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    return isinstance(value, int)


def scan(cards: list[dict]) -> tuple[list[tuple[str, str, object]], list[tuple[str, str, object]]]:
    """Вернуть (заглушки-строки, прочие неканонические значения)."""
    placeholders: list[tuple[str, str, object]] = []
    broken: list[tuple[str, str, object]] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        cid = str(card.get("id") or card.get("name") or "?")
        for field in FIELDS:
            if field not in card:
                continue
            value = card[field]
            if value is None or is_canonical(value):
                continue
            if isinstance(value, str) and value.strip() in PLACEHOLDERS:
                placeholders.append((cid, field, value))
            else:
                broken.append((cid, field, value))
    return placeholders, broken


def normalize(cards: list[dict]) -> int:
    """Заменить строки-заглушки на null. Вернуть число правок."""
    fixed = 0
    for card in cards:
        if not isinstance(card, dict):
            continue
        for field in FIELDS:
            value = card.get(field)
            if isinstance(value, str) and value.strip() in PLACEHOLDERS:
                card[field] = None
                fixed += 1
    return fixed


def dump_like_original(path: Path, data) -> None:
    """Записать JSON, сохранив перевод строки исходного файла.

    data.json в рабочей копии на Windows — CRLF и без завершающего \\n;
    обычный write_text сделал бы файл «переписанным целиком» и спрятал
    настоящий diff из 76 значений в шуме переносов строк.
    """
    raw = io.open(path, encoding="utf-8", newline="").read()
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if newline != "\n":
        text = text.replace("\n", newline)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main() -> int:
    ap = argparse.ArgumentParser(description="Нормализация типов wiki/ongoing (DATA-05)")
    ap.add_argument("--check", action="store_true",
                    help="только проверить типы, ничего не писать (для CI)")
    args = ap.parse_args()

    ru_raw = load(DATA_RU)
    cards = ru_cards(ru_raw)
    en_raw = load(DATA_EN)
    en = en_cards(en_raw)

    ru_placeholders, ru_broken = scan(cards)
    en_placeholders, en_broken = scan(en)

    broken = ru_broken + en_broken
    placeholders = ru_placeholders + en_placeholders

    if args.check:
        if broken or placeholders:
            print(f"[FAIL] типы wiki/ongoing не канонические: "
                  f"заглушек {len(placeholders)}, прочих {len(broken)}", file=sys.stderr)
            for cid, field, value in (placeholders + broken)[:10]:
                print(f"       {cid}: {field} = {value!r} ({type(value).__name__})", file=sys.stderr)
            print("       исправить: python scripts/normalize_wiki_ongoing.py", file=sys.stderr)
            return 1
        print(f"[OK] wiki/ongoing: {len(cards)} карточек RU + {len(en)} EN, "
              f"тип int или null везде")
        return 0

    if broken:
        print("[FAIL] есть значения не из списка заглушек — миграция остановлена, "
              "разберите их руками:", file=sys.stderr)
        for cid, field, value in broken[:20]:
            print(f"       {cid}: {field} = {value!r} ({type(value).__name__})", file=sys.stderr)
        return 1

    fixed_ru = normalize(cards)
    fixed_en = normalize(en)
    if fixed_ru:
        dump_like_original(DATA_RU, ru_raw)
    if fixed_en:
        dump_like_original(DATA_EN, en_raw)

    print(f"[OK] заменено на null: RU {fixed_ru}, EN {fixed_en}")
    for cid, field, value in ru_placeholders[:5]:
        print(f"     {cid}: {field} {value!r} -> null")
    return 0


if __name__ == "__main__":
    sys.exit(main())
