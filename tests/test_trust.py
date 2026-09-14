"""v2.5: доверие — FAQ, глоссарий, журнал правок, ссылки в футерах."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

FAQ = (DOCS / "faq.html").read_text(encoding="utf-8")
GLOSS = (DOCS / "glossary.html").read_text(encoding="utf-8")
CHLOG = (DOCS / "changelog_public.html").read_text(encoding="utf-8")
INDEX = (DOCS / "index.html").read_text(encoding="utf-8")
MAP = (DOCS / "map.html").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

FAQ_QUESTIONS = [
    "Что такое мета-анализ?",
    "Что такое Hedges",
    "Что такое грейд A-D",
    "scienceIndex",
    "Как читать квадрант",
    "цена не найдена",
    "принимать всё сразу",
    "Когда ждать эффект",
]

GLOSS_TERMS = ["Мета-анализ", "РКИ", "Hedges' g", "CI (доверительный интервал)",
               "Science Index", "Грейд", "Вердикт", "Биодоступность",
               "Синергист", "Антагонист", "UL (upper limit)", "Onset"]


def test_faq_renders_8_questions():
    assert FAQ.count("<details class=\"qa\"") == 8, "faq.html: должно быть 8 аккордеонов"
    for q in FAQ_QUESTIONS:
        assert q in FAQ, f"нет вопроса в FAQ: {q}"


def test_glossary_renders_12_terms():
    assert GLOSS.count("<tr") >= 13, "glossary.html: таблица без строк"
    for term in GLOSS_TERMS:
        assert term in GLOSS, f"нет термина в глоссарии: {term}"


def test_changelog_public_renders_history():
    versions = re.findall(r"<td>v2\.\d(?:\.\d)?</td>", CHLOG)
    assert len(versions) >= 4, f"changelog_public.html: версий {len(versions)}"
    for v in ["v2.1", "v2.2", "v2.3", "v2.4", "v2.4.1"]:
        assert f">{v}</td>" in CHLOG, f"журнал правок не содержит {v}"


def test_footer_links_on_index():
    for target in ["faq.html", "glossary.html", "changelog_public.html", "methodology.html"]:
        assert f"href=\"{target}\"" in INDEX, f"index.html: нет ссылки на {target}"


def test_footer_links_on_map():
    for target in ["faq.html", "glossary.html", "changelog_public.html", "methodology.html"]:
        assert f"href=\"{target}\"" in MAP, f"map.html: нет ссылки на {target}"


def test_changelog_md_has_v25_block():
    assert "## [v2.5]" in CHANGELOG, "CHANGELOG.md: нет блока [v2.5]"