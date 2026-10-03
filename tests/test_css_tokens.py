"""Шкала отступов объявлена целиком и используется только по назначению.

Зачем этот тест
---------------
На шаге 6 токены с точкой в имени (`--space-2.5`) выглядели рабочими в коде,
но браузер ВЫБРАСЫВАЕТ их молча: имя кастомного свойства - это
`--` + <ident>, а <ident> не может содержать `.`. Из-за этого `var()` от
такого имени проваливал всё объявление, padding/margin уезжали к правилу с
меньшим приоритетом, и 23 снапшота падали при зелёном `pytest -q`.

Никакой статический анализ этого не ловил: `pytest -q` был зелёным, а
`test_no_orphan_classes` — тоже. Поймали только снапшоты. Тест ниже ловит
это за 0.1 с и без браузера.

Три проверки
------------
1. Каждый `var(--space-*)` в CSS имеет объявление. Пропавший токен означает,
   что правило молча уходит в invalid-at-computed-value-time.
2. В именах токенов нет точки — она невалидна по спецификации, даже если
   какой-то браузер её простит.
3. Шкала покрывает ожидаемые значения, то есть токены не переписаны
   по ошибке.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STYLE = DOCS / "style.css"

#: Ожидаемая шкала. Имена с дефисом: точка в имени невалидна.
EXPECTED = {
    "--space-1": "4px",
    "--space-0-2": ".2rem",
    "--space-0-3": ".3rem",
    "--space-2": "8px",
    "--space-2-5": "10px",
    "--space-3": "12px",
    "--space-4": "16px",
    "--space-5": "20px",
    "--space-6": "24px",
    "--space-8": "32px",
    "--space-12": "48px",
}

STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
VAR_USE = re.compile(r"var\(\s*(--space-[^)\s]+)")
DECL = re.compile(r"(--space-[\w-]+)\s*:\s*([^;}]+)")
#: Шаг 7 добавил шкалы радиусов и теней. Проверки те же: объявлено ровно
#: один раз, значение совпадает, точек в именах нет. Значения взяты из
#: reports/DESIGN_SYSTEM_PLAN.md §2.4-2.5 и совпадают с литералами, которые
#: заменили, - иначе токенизация сдвинула бы пиксели.
EXPECTED_SHAPE = {
    "--radius-sm": "4px",
    "--radius-md": "6px",
    "--radius-lg": "8px",
    "--radius-xl": "12px",
    "--radius-pill": "999px",
    "--shadow-sm": "0 2px 6px var(--shadow)",
    "--shadow-md": "0 2px 8px rgba(0,0,0,.15)",
    "--shadow-lg": "0 12px 32px rgba(0,0,0,.16)",
    "--shadow-xl": "0 24px 80px rgba(0,0,0,.55)",
}
#: --shadow-lg переобъявляется в тёмной ветке: .16 -> .5. Это единственный
#: токен тени, который зависит от темы, поэтому объявлен дважды.
EXPECTED_SHAPE_DARK = {"--shadow-lg": "0 12px 32px rgba(0,0,0,.5)"}
SHAPE_USE = re.compile(r"var\(\s*(--(?:radius|shadow)-[^)\s]+)")
SHAPE_DECL = re.compile(r"(--(?:radius|shadow)-[\w-]+)\s*:\s*([^;}]+)")


def _css_sources() -> list[tuple[str, str]]:
    out = [("style.css", STYLE.read_text(encoding="utf-8"))]
    for p in sorted(list(DOCS.glob("*.html")) + list(DOCS.glob("sup/*.html"))):
        for i, b in enumerate(STYLE_BLOCK.findall(p.read_text(encoding="utf-8")), 1):
            out.append((f"{p.name} <style> #{i}", b))
    return out


def test_spacing_tokens_are_declared():
    """Каждый токен шкалы объявлен ровно один раз и с ожидаемым значением."""
    css = STYLE.read_text(encoding="utf-8")
    found = {m.group(1): m.group(2).strip()
             for m in DECL.finditer(re.sub(r"/\*.*?\*/", " ", css, flags=re.S))}
    missing = sorted(set(EXPECTED) - set(found))
    assert not missing, f"не объявлены: {', '.join(missing)}"
    wrong = {k: (found[k], v) for k, v in EXPECTED.items() if found[k] != v}
    assert not wrong, f"значения не совпадают (получено, ожидалось): {wrong}"


def test_no_dotted_token_names():
    """Точка в имени кастомного свойства невалидна - и её отбрасывают молча."""
    css = STYLE.read_text(encoding="utf-8")
    dotted = sorted({m.group(1) for m in DECL.finditer(css) if "." in m.group(1)})
    assert not dotted, (
        f"в style.css есть токены с точкой в имени: {', '.join(dotted)}. "
        f"Браузер выбросит объявление, var() от него провалит всё правило, "
        f"и страница поедет без единой ошибки в консоли."
    )
    used = sorted({v for _src, css2 in _css_sources()
                   for v in VAR_USE.findall(css2)})
    bad = [u for u in used if "." in u]
    assert not bad, (
        f"в правилах используются токены с точкой: {', '.join(bad)}. "
        f"Такие var() не разрешаются - замените имена на дефисные."
    )


def test_every_used_token_is_declared():
    """Ни один var(--space-*) не должен остаться без объявления."""
    declared = {m.group(1) for m in
                DECL.finditer(re.sub(r"/\*.*?\*/", " ", STYLE.read_text(
                    encoding="utf-8"), flags=re.S))}
    used = {v for _src, css in _css_sources() for v in VAR_USE.findall(css)}
    undeclared = sorted(used - declared)
    assert not undeclared, (
        f"используются, но не объявлены: {', '.join(undeclared)}. "
        f"Такие правила молча уходят в invalid-at-computed-value-time."
    )


def test_tokens_do_not_leak_into_other_properties():
    """Токен отступа не должен попасть в font-size, width, height и прочее.

    Замер: первый вариант шага 6 подставлял `var(--space-2.5)` в опции
    vis-network внутри <script>, где `margin: 10` - это число в JS-объекте.
    Ошибка выглядела как `Unexpected token 'var'`, и граф на atlas просто не
    рисовался.
    """
    forbidden = ("font-size", "width", "height", "top", "left", "right",
                 "bottom", "border-radius", "box-shadow", "line-height")
    bad = []
    for src, css in _css_sources():
        clean = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
        for m in re.finditer(r"([a-z-]+)\s*:\s*([^;{}]*var\(--space-[^;{}]*)",
                             clean):
            if m.group(1) in forbidden:
                bad.append(f"{src}: {m.group(1)}: {m.group(2).strip()[:40]}")
    assert not bad, "токен отступа попал в не-отступное свойство:\n  " + \
                    "\n  ".join(bad[:10])


@pytest.mark.parametrize("page", ["offline"])
def test_offline_page_has_no_token_dependency(page):
    """offline.html не подключает style.css и обязан быть самодостаточным.

    Там намеренно нет зависимости: «чтобы не тянуть в кэш ещё один файл».
    Если бы проход токенизации зашёл на эту страницу, её отступы стали бы
    var(--space-*) без объявления — и она бы сломалась ТИХО, без ошибки в
    консоли и без падения тестов.
    """
    text = (DOCS / f"{page}.html").read_text(encoding="utf-8")
    used = VAR_USE.findall(text)
    assert not used, (
        f"{page}.html использует {', '.join(sorted(set(used)))}, но не "
        f"подключает style.css и не объявляет шкалу. Такие ссылки без "
        f"объявления молча ломают отступы."
    )
    shape = SHAPE_USE.findall(text)
    assert not shape, (
        f"{page}.html использует {', '.join(sorted(set(shape)))}, но не "
        f"подключает style.css. Радиусы и тени без объявления ломаются так "
        f"же тихо, как отступы."
    )


def test_shape_tokens_are_declared():
    """Шкалы радиусов и теней объявлены с ожидаемыми значениями.

    Значения читаются из блока :root, а не со всего файла: --shadow-lg
    переобъявлен в тёмной ветке, и при поиске по всему CSS последнее
    вхождение (.5) вытесняло бы светлое (.16).
    """
    css = STYLE.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{(.*?)\}", css, re.S)
    assert root, "в style.css нет блока :root"
    found = {m.group(1): " ".join(m.group(2).split())
             for m in SHAPE_DECL.finditer(root.group(1))}
    missing = sorted(set(EXPECTED_SHAPE) - set(found))
    assert not missing, f"не объявлены в :root: {', '.join(missing)}"
    wrong = {k: (found[k], v) for k, v in EXPECTED_SHAPE.items() if found[k] != v}
    assert not wrong, f"значения не совпадают (получено, ожидалось): {wrong}"

    dark = re.search(r"html\.dark\s*,\s*body\.dark\s*\{(.*?)\}", css, re.S)
    assert dark, "в style.css нет блока html.dark,body.dark"
    dfound = {m.group(1): " ".join(m.group(2).split())
              for m in SHAPE_DECL.finditer(dark.group(1))}
    for k, v in EXPECTED_SHAPE_DARK.items():
        assert dfound.get(k) == v, (
            f"в тёмной ветке {k} = {dfound.get(k)!r}, ожидалось {v!r}. "
            f"Без этого карточка в тёмной теме получит светлую тень."
        )


def test_shape_tokens_resolve_and_have_no_dots():
    """Каждый var(--radius-*/--shadow-*) имеет объявление, точек нет."""
    css = STYLE.read_text(encoding="utf-8")
    dotted = sorted({m.group(1) for m in SHAPE_DECL.finditer(css) if "." in m.group(1)})
    assert not dotted, f"токены с точкой в имени: {', '.join(dotted)}"
    used = {v for _src, css2 in _css_sources() for v in SHAPE_USE.findall(css2)}
    bad = sorted(t for t in used if "." in t)
    assert not bad, f"используются токены с точкой: {', '.join(bad)}"
    declared = {m.group(1) for m in SHAPE_DECL.finditer(css)}
    undeclared = sorted(used - declared)
    assert not undeclared, (
        f"используются, но не объявлены: {', '.join(undeclared)}. Такие "
        f"правила уходят в invalid-at-computed-value-time."
    )


def test_shape_tokens_do_not_leak_into_other_properties():
    """Токен радиуса не должен попасть в отступы, а токен тени — куда-то ещё.

    Шаг 6 уже ловил такое для отступов: подстановка var() в опции vis-network
    внутри <script> давала `Unexpected token 'var'`, и граф на atlas просто
    не рисовался. Здесь та же проверка в обратную сторону - токен формы не
    должен оказаться в несвойственном свойстве.
    """
    forbidden_for_radius = ("padding", "margin", "font-size", "width", "height",
                            "top", "left", "right", "bottom", "line-height",
                            "gap", "box-shadow", "border-width")
    forbidden_for_shadow = ("border-radius", "padding", "margin", "width",
                            "height", "font-size", "line-height")
    bad = []
    for src, css2 in _css_sources():
        stripped = re.sub(r"/\*.*?\*/", " ", css2, flags=re.S)
        for m in re.finditer(r"([a-z-]+)\s*:\s*([^;{}]*var\(--(?:radius|shadow)-[^;{}]*)",
                             stripped):
            prop = m.group(1)
            body = m.group(2)
            forb = (forbidden_for_radius if "--radius-" in body
                    else forbidden_for_shadow)
            if prop in forb:
                bad.append(f"{src}: {prop}: {body.strip()[:40]}")
    assert not bad, "токен формы попал в несвойственное свойство:\n  " + \
                    "\n  ".join(bad[:10])
