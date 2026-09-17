"""Unit-тесты для scripts/validate_sources.py."""
import json
from datetime import datetime, timedelta, timezone

from scripts.validate_sources import _days_since, _safe_year


def test_safe_year():
    assert _safe_year("2024") == 2024
    assert _safe_year("?") == 0
    assert _safe_year(None) == 0


def test_days_since_missing(tmp_path):
    assert _days_since(tmp_path / ".last_validation") is None


def test_days_since_fresh(tmp_path):
    marker = tmp_path / ".last_validation"
    marker.write_text(
        json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    d = _days_since(marker)
    assert d is not None
    assert 0 <= d < 1


def test_days_since_stale(tmp_path):
    marker = tmp_path / ".last_validation"
    old = datetime.now(timezone.utc) - timedelta(days=100)
    marker.write_text(json.dumps({"timestamp": old.isoformat()}), encoding="utf-8")
    d = _days_since(marker)
    assert d is not None
    assert 99 <= d <= 101


def test_days_since_corrupted(tmp_path):
    marker = tmp_path / ".last_validation"
    marker.write_text("не json", encoding="utf-8")
    assert _days_since(marker) is None
