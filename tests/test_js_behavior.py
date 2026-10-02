"""Поведение docs/script.js без браузера: экранирование, XSS, пустые данные.

QA_AUDIT P2-28 (XSS не покрыт) и P2-31/32 (пустой массив и один элемент).

jsdom в проекте нет, а Chromium в CI не установлен (в workflows/tests.yml
нет `playwright install chromium`). Поэтому тесты/js_harness.js загружает
САМ script.js на минимальном DOM-шиме, выполняет настоящий код renderCards()/esc()
и печатает JSON; этот файл разбирает результат и делает assert.

Стенд НЕ копирует функции: если esc() сломать в script.js, тесты упадут.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "js_harness.js"
SCRIPT_JS = ROOT / "docs" / "script.js"
NODE = shutil.which("node")


@pytest.fixture(scope="module")
def js():
    if NODE is None:
        pytest.skip("node не установлен")
    if not SCRIPT_JS.exists():
        pytest.skip(f"нет {SCRIPT_JS}")
    import os
    env = dict(os.environ, SCRIPT_JS=str(SCRIPT_JS))
    r = subprocess.run([NODE, str(HARNESS)], capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=str(ROOT), timeout=60)
    if not r.stdout.strip():
        pytest.fail(f"стенд не выдал JSON (rc={r.returncode}).\nstdout={r.stdout!r}\nstderr={r.stderr!r}")
    data = json.loads(r.stdout)
    if not data.get("ok"):
        pytest.fail(f"стенд упал: {data.get('errors')}\n{data.get('stack', '')}")
    return data["results"]


# ═══════════════════════ esc(): экранирование (P2-28) ═══════════════════════

@pytest.mark.parametrize("key,expected", [
    ("lt", "&lt;"),
    ("gt", "&gt;"),
    ("amp", "&amp;"),
    ("dq", "&quot;"),
    ("sq", "&#39;"),
])
def test_esc_escapes_five_dangerous_chars(js, key, expected):
    """Пять символов, которые обязаны быть экранированы: без них
    внедрение атрибута и текста ломает разметку."""
    assert js["esc"][key] == expected


def test_esc_escapes_ampersand_first(js):
    """& экранируется ПЕРВЫМ. Иначе «&lt;» из данных превратится в «<»,
    то есть двойное декодирование — классический обход экранирования."""
    assert js["esc"]["amp_first"] == "&amp;lt;"
    assert "<" not in js["esc"]["amp_first"]


def test_esc_full_script_tag_is_inert(js):
    out = js["esc"]["script"]
    assert out == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert "<" not in out and ">" not in out


def test_esc_img_onerror_is_inert(js):
    out = js["esc"]["img_onerror"]
    assert "<" not in out and ">" not in out
    assert out.startswith("&lt;img")


def test_esc_leaves_slash_and_backslash(js):
    """Слэш НЕ экранируется — и это правильно: в текстовом узле HTML
    «/» не имеет специального значения. Проверяем явно, чтобы изменение
    поведения не проскочило незамеченным (и чтобы никто не «починил»
    лишним replace без вреда, но с ложной уверенностью в безопасности)."""
    assert js["esc"]["slash"] == "/"
    assert js["esc"]["backslash"] == "\\"


def test_esc_keeps_cyrillic_and_mixed_script(js):
    """Экранирование не должно ломать читаемость кириллицы."""
    assert js["esc"]["cyr"] == "Креатин"
    assert js["esc"]["mixed"] == "Л-Теанин (L-theanine)"


@pytest.mark.parametrize("key,expected", [("null_", ""), ("undef", ""), ("num", "42")])
def test_esc_handles_non_strings(js, key, expected):
    """esc() получает s.category || '' и прочие значения, которые могут
    быть null/undefined/числом. null не должен давать «null» в тексте."""
    assert js["esc"][key] == expected


# ═══════════════════════ XSS-инъекция через данные карточки ═══════════════════════

def test_injected_card_produces_no_script_tag(js):
    """Все поля карточки наполнены payload'ами вида
    <script>window.__pwned=N</script>. В выводе не должно быть сырых тегов."""
    x = js["xss"]
    assert x["hasRawScript"] is False, f"в разметке остался сырой <script>: {x['html'][:400]}"
    assert x["hasRawImg"] is False, "остался сырой <img onerror>"
    assert x["hasRawSvg"] is False, "остался сырой <svg onload>"


def test_injected_card_no_attribute_breakout(js):
    """category = '\"><script>…' — классическая попытка вырваться из
    атрибута. Кавычка должна быть экранирована, иначе атрибут закроется
    и начнётся новый тег."""
    assert js["xss"]["hasQuoteBreakout"] is False, "инъекция через значение атрибута"


def test_injected_card_escaped_forms_present(js):
    """Обратная проверка: экранированные формы обязаны быть в разметке,
    иначе тесты выше проходили бы из-за того, что payload вообще не
    попал в вывод (например, поле перестало рендериться)."""
    x = js["xss"]
    assert x["hasEscapedScript"] is True
    assert x["hasEscapedImg"] is True
    assert x["hasEscapedSvg"] is True


def test_injected_card_code_never_executed(js):
    """window.__pwned остаётся неопределённым: ни один обработчик не
    выполнился, скрипт не исполнился."""
    assert js["xss"]["pwned"] in (None, 0), f"payload исполнился: __pwned={js['xss']['pwned']}"


def test_bare_onerror_text_is_harmless(js):
    """'onerror=alert(1)' остаётся в тексте — и это нормально: тега нет,
    браузер нечего выполнять. Фиксируем намерение, чтобы будущий «рефакторинг»
    не решил, что это уязвимость, и не сломал бы экранирование зря."""
    assert js["xss"]["hasBareOnerrorEq"] is True
    assert js["xss"]["hasRawImg"] is False


# ═══════════════════════ renderCards: пустые и единичные данные (P2-31, 32) ═══════════════════════

def test_render_cards_empty_array_shows_empty_state(js):
    """Главный путь деградации: данных нет, но страница обязана показать
    понятное пустое состояние, а не упасть и не остаться белой."""
    e = js["empty"]
    assert e["noCards"] is True
    assert e["hasEmptyClass"] is True
    assert e["saysNothingFound"] is True
    assert e["hasResetButton"] is True, "в пустом состоянии должна быть кнопка сброса фильтров"


def test_render_cards_empty_state_has_no_undefined(js):
    assert "undefined" not in js["empty"]["html"]


def test_render_cards_single_element(js):
    """Граница снизу: массив из одной карточки. Никаких top-N/slice(-90)
    не применяется, но рендер обязан быть корректным."""
    s = js["single"]
    assert s["cards"] == 1
    assert s["hasName"] is True
    assert s["hasUndefined"] is False
    assert s["hasNaN"] is False
    assert s["hasNullText"] is False


def test_render_cards_minimal_card_no_leaking_placeholders(js):
    """Карточка без effects/updated/rct — минимальный контракт.
    В разметку не должны просочиться undefined/NaN/null."""
    m = js["minimal"]
    assert m["cards"] == 1
    assert m["hasUndefined"] is False
    assert m["hasNaN"] is False


def test_harness_loaded_real_script(js):
    """Стенд обязан экспортировать функции из script.js — иначе он молча
    тестирует сам себя (пустой вызов вернул бы ошибку, но полезно убедиться
    явно, что скрипт прочитан)."""
    for fn in ("renderCards", "esc"):
        assert fn in js["exported"], f"стенд не получил {fn} из script.js"
