"""Цифры в скиллах не должны протухать молча.

Зачем этот тест
---------------
SK-STALE-03: `.opencode/skills/visual-design-audit/SKILL.md` приводит
проектные числа как иллюстрации («118 hardcoded hex», «24 font-size»,
«11 разных box-shadow», «4 градиента»). Эти числа мгновенно устаревают:
любая правка CSS расшатывает их, а проверить их некому — скилл не
исполняется, его читают глазами.

Как это выглядит на практике
----------------------------
Проверка 2026-10-12 показала расхождение по всем четырём:

| Метрика            | В скилле | Фактически |
|--------------------|----------|------------|
| hardcoded hex      | 118      | **96**     |
| разных font-size   | 24       | **17**     |
| разных box-shadow  | 11       | **15**     |
| градиентов         | 4        | **6**      |

То есть скилл описывал картину, которой в проекте нет уже давно. И
наоборот: `box-shadow` он недооценивал вчетверо — то есть подталкивал
искать дубли там, где их нет, и не замечать реальные.

Что этот тест делает
--------------------
Не запрещает числа, а требует, чтобы они были правдой. Метрики
пересчитываются из `docs/style.css` при каждом прогоне, и расхождение
валит тест с обеими величинами в сообщении: «в скилле X, в проекте Y».
Обновить нужно оба числа, иначе тест продолжит падать.

Границы подсчёта
----------------
Сложность здесь в том, чтобы не попасть в две ловушки.

**Комментарии исключены.** В `style.css` есть комментарии, где цвет и
тень упоминаются словами («возврат к фиолетовому из-за контраста»).
Считать их дало бы завышенные числа, а скилл описывает реальные
объявления.

**Значения в комментариях исключены, объявления — нет.** Объявление
`--accent-2: #8ecbff` в `:root` содержит hex, но это *объявление
токена*, то есть ровно то, чего скилл советует не иметь. Считать его
хардкодом нельзя: иначе число растёт от каждой новой переменной.

Поэтому hardcoded hex считаются только там, где цвет записан мимо
переменной:

    объявление  ->  значение содержит #HEX   ->  ТОКЕН (не считаем)
    свойство     ->  значение содержит #HEX   ->  ХАРДКОД (считаем)

Ровно та же развилка, что и в `test_css_tokens.py`, где объявления
токенов внутри `:root` тоже не считаются хардкодами.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "docs" / "style.css"
SKILL = ROOT / ".opencode" / "skills" / "visual-design-audit" / "SKILL.md"

#: Что проверяем: ключ в тексте скилла -> как посчитать в style.css.
METRICS = {
    "hardcoded hex": "hardcoded_hex",
    "разных `font-size`": "font_sizes",
    "разных `box-shadow`": "box_shadows",
    # «градиент», а не «градиента»: число в скилле стоит перед словом и
    # склоняется по числа («4 градиента», но «6 градиентов»). Именно на
    # этом упал первый прогон после правки числа.
    "градиент": "gradients",
    # Число CSS-переменных добавлено в батче 7 (HC-P1-03). Раньше оно
    # стояло в скилле («против 7 CSS-переменных») и не проверялось гейтом
    # — поэтому и протухло: 7 против фактических 106 объявлений `--var:`.
    "CSS-переменных": "css_vars",
}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
GRADIENT = re.compile(r"(linear|radial|conic)-gradient\(")
COMMENT = re.compile(r"/\*.*?\*/", re.S)
DECL = re.compile(r"(--[\w-]+)\s*:\s*([^;}]*)")


def _strip_comments(css: str) -> str:
    """Комментарии не считаются ничем: ни хардкодами, ни правилами."""
    return COMMENT.sub(" ", css)


def _measure() -> dict[str, int]:
    css = _strip_comments(STYLE.read_text(encoding="utf-8"))

    # Хардкод — это цвет, записанный в свойстве. Цвет в объявлении
    # токена (--name: #hex) наоборот является целью токенизации и
    # хардкодом не считается.
    tokens: set[str] = set()
    token_values: list[str] = []
    for m in DECL.finditer(css):
        name, value = m.group(1), m.group(2)
        tokens.add(name)
        if HEX.search(value):
            token_values.append(value)

    token_hexes = {h.lower() for v in token_values for h in HEX.findall(v)}

    hardcoded = 0
    for chunk in css.split(";"):
        if ":" not in chunk:
            continue
        prop, _, value = chunk.partition(":")
        if prop.strip().startswith("--"):
            continue
        for h in HEX.findall(value):
            if h.lower() not in token_hexes:
                hardcoded += 1

    return {
        "hardcoded_hex": hardcoded,
        "font_sizes": len({v.strip() for v in re.findall(
            r"font-size:\s*([^;}]+)", css)}),
        "box_shadows": len({v.strip() for v in re.findall(
            r"box-shadow:\s*([^;}]+)", css)}),
        "gradients": len(GRADIENT.findall(css)),
        "css_vars": len(DECL.findall(css)),
    }


def test_metrics_have_a_measured_value():
    """Страховка: каждая метрика обязана что-то возвращать.

    Иначе словарь с нулями прошёл бы сравнение «в скилле 0, в проекте 0».
    """
    m = _measure()
    empty = sorted(k for k, v in m.items() if v == 0)
    assert not empty, (
        f"Метрики вернули ноль: {', '.join(empty)}. Метрика перестала "
        f"измерять то, для чего написана, и пропускает расхождение."
    )


def test_skill_numbers_match_the_project():
    """Цифры в скилле == цифры в style.css."""
    measured = _measure()
    text = SKILL.read_text(encoding="utf-8")

    drift = []
    for needle, metric in METRICS.items():
        actual = measured[metric]
        # Число в скилле стоит ПЕРЕД названием метрики («118 hardcoded
        # hex», «4 градиента»), поэтому ищем пару в этом порядке.
        # Поиск наоборот находил число из соседней строки и сравнивал
        # не с тем, что имелось в виду.
        m = re.search(r"(\d+)\s*" + re.escape(needle), text)
        if not m:
            drift.append(f"{metric}: в скилле нет числа рядом с {needle!r}")
            continue
        claimed = int(m.group(1))
        if claimed != actual:
            drift.append(
                f"{metric}: в скилле {claimed}, в проекте {actual}"
            )

    assert not drift, (
        "Цифры в скилле разошлись с проектом (SK-STALE-03):\n"
        + "\n".join("  " + d for d in drift)
        + "\n\nСкилл учит искать дубли по этим числам. Неверное число "
          "либо скрывает реальный дубль, либо указывает на пустое место."
    )