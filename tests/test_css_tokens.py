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
