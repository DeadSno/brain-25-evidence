"""Гард: meta charset=utf-8 — ПЕРВЫЙ тег внутри <head> каждого docs/*.html."""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

CHARSET_FIRST = re.compile(r"<head>\s*<meta\s+charset\s*=", re.IGNORECASE | re.DOTALL)


def test_all_html_charset_first_in_head():
    html_files = list(DOCS.glob("*.html"))
    assert len(html_files) > 0, "нет HTML-файлов в docs/"

    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        assert CHARSET_FIRST.search(content) is not None, \
            f"{html_file.name}: <meta charset> — не первый тег внутри <head>"


def test_serve_py_exists():
    serve = Path(__file__).resolve().parents[1] / "docs" / "serve.py"
    assert serve.exists(), "docs/serve.py не создан"