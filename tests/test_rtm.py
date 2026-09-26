"""Тесты для RTM — покрытие требований."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTM = ROOT / "docs" / "rtm.md"
US = ROOT / "docs" / "user_stories.md"
NFR = ROOT / "docs" / "nfr.md"


def test_rtm_exists():
    assert RTM.exists(), "docs/rtm.md не найден"


def test_user_stories_exists():
    assert US.exists(), "docs/user_stories.md не найден"


def test_nfr_exists():
    assert NFR.exists(), "docs/nfr.md не найден"


def test_all_us_mentioned_in_rtm():
    """Все US-01...US-09 из user_stories должны быть в RTM."""
    us_text = US.read_text(encoding="utf-8")
    rtm_text = RTM.read_text(encoding="utf-8")
    for i in range(1, 10):
        us_id = f"US-{i:02d}"
        assert us_id in us_text, f"{us_id} не в user_stories.md"
        assert us_id in rtm_text, f"{us_id} не в rtm.md"


def test_rtm_has_status_legend():
    txt = RTM.read_text(encoding="utf-8")
    assert "done" in txt or "Легенда" in txt, "RTM без легенды статусов"


def test_rtm_has_coverage_table():
    txt = RTM.read_text(encoding="utf-8")
    assert "Покрытие" in txt or "покрыт" in txt.lower(), "RTM без таблицы покрытия"
