"""F5: структура компактных блоков доверия в index.html.

- #qaSection содержит .qaGrid с 3 карточками
- #trustSummary содержит .trustChips с 5 чипами
- #chartSummary элемент есть (для подписи под чартом F2.2)
"""
import re
from pathlib import Path

INDEX = (Path(__file__).resolve().parents[1] / "docs" / "index.html").read_text(encoding="utf-8")
HTML_NO_COMMENTS = re.sub(r"<!--.*?-->", "", INDEX, flags=re.S)


def test_qa_grid_exists():
    assert 'qaGrid' in HTML_NO_COMMENTS, "нет qaGrid в index.html"
    assert HTML_NO_COMMENTS.count("qaGrid") >= 1, "qaGrid не найден в index.html"


def test_qa_three_cards():
    qa_cards = re.findall(r'<div class="qa">', HTML_NO_COMMENTS)
    assert len(qa_cards) == 3, f"ожидается 3 карточки .qa в qaGrid, найдено {len(qa_cards)}"


def test_trust_chips_structure():
    assert 'trustChips' in HTML_NO_COMMENTS, "нет trustChips в index.html"
    assert HTML_NO_COMMENTS.count('class="chip"') >= 5, \
        f"ожидается ≥5 чипов в trustChips, найдено {HTML_NO_COMMENTS.count('class=\"chip\"')}"


def test_chart_summary_element():
    assert "chartSummary" in INDEX, "нет #chartSummary для подписи под чартом F2.2"
