"""Unit-тесты для scripts/apply_sources.py."""
from scripts.apply_sources import _slim


def test_slim_keeps_essentials_drops_meta():
    entry = {
        "pmid": "123",
        "score": 3,
        "resolved_name": "X",
        "title": "T",
        "year": 2024,
        "journal": "J",
        "pubtype": ["Meta-Analysis"],
        "source": "curated",
    }
    s = _slim(entry)
    assert "score" not in s
    assert "resolved_name" not in s
    assert s["pmid"] == "123"
    assert s["title"] == "T"
    assert s["year"] == 2024
    assert s["journal"] == "J"
    assert s["pubtype"] == ["Meta-Analysis"]
    assert s["source"] == "curated"


def test_slim_defaults_for_missing_fields():
    s = _slim({"pmid": "123"})
    assert s["pmid"] == "123"
    assert s["title"] == "?"
    assert s["year"] == 0
    assert s["journal"] == "?"
    assert s["pubtype"] == []
    assert s["source"] == "curated"
