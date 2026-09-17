"""Unit-тесты для scripts/migrate_key_sources.py."""
from scripts.migrate_key_sources import _safe_year, make_entry


def test_safe_year_valid():
    assert _safe_year("2024 Jan") == 2024
    assert _safe_year("2024") == 2024
    assert _safe_year("1999 Dec-Feb") == 1999


def test_safe_year_invalid():
    assert _safe_year("?") == 0
    assert _safe_year("") == 0
    assert _safe_year(None) == 0
    assert _safe_year("abcd") == 0


def test_make_entry_with_meta():
    meta = {"title": "T", "year": 2024, "journal": "J", "pubtype": ["Meta-Analysis"]}
    e = make_entry("12345", meta)
    assert e["pmid"] == "12345"
    assert e["title"] == "T"
    assert e["year"] == 2024
    assert e["journal"] == "J"
    assert e["pubtype"] == ["Meta-Analysis"]


def test_make_entry_without_meta():
    """meta=None — PMID не найден в PubMed, честная пометка без выдумок."""
    e = make_entry("99999999", None)
    assert e["pmid"] == "99999999"
    assert "не найден" in e["title"]
    assert e["year"] == 0
    assert e["journal"] == "?"


def test_make_entry_preserves_pubtype():
    meta = {"title": "T", "year": 2020, "journal": "J", "pubtype": ["RCT", "Journal Article"]}
    e = make_entry("1", meta)
    assert e["pubtype"] == ["RCT", "Journal Article"]
