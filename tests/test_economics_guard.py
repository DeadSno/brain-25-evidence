"""Гард v2.6.1: демонтаж Value Score завершён.

В docs/script.js и docs/index.html не встречаются подстроки «Ценность»,
«Value Score», «valueScore» В РЕНДЕРЕ. Комментарии и историческая
документация допустимы, поэтому сканируем только строковые литералы JS
и текст index.html вне HTML-комментариев.
"""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
FORBIDDEN = ["Ценность", "Value Score", "valueScore"]

SCRIPT = (DOCS / "script.js").read_text(encoding="utf-8")
INDEX = (DOCS / "index.html").read_text(encoding="utf-8")

JS_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
JS_STRING = re.compile(
    r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`(?:[^`\\]|\\.)*`", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _js_literals(src: str) -> list[str]:
    no_comments = JS_COMMENT.sub(" ", src)
    return JS_STRING.findall(no_comments)


def test_script_js_literals_no_value_score():
    bad = [(tok, lit) for lit in _js_literals(SCRIPT) for tok in FORBIDDEN if tok in lit]
    assert not bad, f"в строковых литералах script.js найден демонтируемый термин: {bad[:3]}"


def test_index_html_no_value_score():
    no_comments = HTML_COMMENT.sub(" ", INDEX)
    hits = [w for w in FORBIDDEN if w in no_comments]
    assert not hits, f"в index.html (вне комментариев) найден демонтируемый термин: {hits}"


def test_sort_options_positive():
    # сортировки должны остаться: по доказательности, по цене, по алфавиту, по грейду
    html = HTML_COMMENT.sub(" ", INDEX)
    for option in ['value="science"', 'value="price_asc"', 'value="name"', 'value="grade"']:
        assert option in html, f"{option} пропал из #sortSelect"
    assert 'value="value"' not in html, "опция «по ценности» не удалена"