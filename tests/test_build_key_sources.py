"""Тесты идемпотентности scripts/build_key_sources.py (QA-P1-2, DATA-P1-1).

Контекст. До фикса скрипт на двух ветках присваивал `s["ma_top3"] = []`:

  * ветка «нет запроса в SUPPLEMENTS» — 56 карточек, 165 PMID;
  * ветка `except RuntimeError` — любая сетевая ошибка у карточек с запросом.

Обе ветки срабатывали при КАЖДОМ повторном запуске, то есть один прогон по сети
из 74 карточек с запросом обнулял 165 уже собранных PMID. Тесты ниже проверяют,
что этого больше не происходит.

Сеть не используется: `top3_ma` и `summaries` подменяются заглушками,
`DATA` — временным файлом. Живой `docs/data.json` тесты не пишут.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_key_sources as bks  # noqa: E402
from src.config import SUPPLEMENTS  # noqa: E402

#: Имя вне SUPPLEMENTS — карточка без запроса (ветка DATA-P1-1).
NO_QUERY_NAME = "Добавка без запроса в SUPPLEMENTS"
#: Имя из SUPPLEMENTS — карточка с запросом (ветка с обновлением ma_top3).
WITH_QUERY_NAME = next(iter(SUPPLEMENTS))

NEW_PMID = "99999999"
NEW_ENTRY = [{"pmid": NEW_PMID, "title": "New meta-analysis", "year": 2026}]


@pytest.fixture
def harness(tmp_path, monkeypatch):
    """Скопировать build_key_sources на временный data.json, сеть отключить."""
    data_path = tmp_path / "data.json"
    state = {"calls": 0}

    def fake_top3_ma(query: str) -> list[str]:
        state["calls"] += 1
        return [NEW_PMID]

    def fake_summaries(pmids: list[str]) -> list[dict]:
        return NEW_ENTRY

    def fail_top3_ma(query: str) -> list[str]:
        raise RuntimeError("PubMed недоступен: HTTP 429")

    monkeypatch.setattr(bks, "DATA", data_path)
    monkeypatch.setattr(bks, "top3_ma", fake_top3_ma)
    monkeypatch.setattr(bks, "summaries", fake_summaries)
    monkeypatch.setattr(bks.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(bks, "SLEEP", 0)

    return {
        "path": data_path,
        "state": state,
        "fail_network": lambda: monkeypatch.setattr(bks, "top3_ma", fail_top3_ma),
    }


def write_cards(path: Path, cards: list[dict]) -> None:
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def card(cards: list[dict], name: str) -> dict:
    return next(c for c in cards if c["name"] == name)


def seed(path: Path) -> None:
    """Две карточки с непустым ma_top3 — то, что обнулять нельзя."""
    write_cards(path, [
        {"id": "no-q", "name": NO_QUERY_NAME,
         "ma_top3": [{"pmid": "11111111", "title": "Kept", "year": 2024}]},
        {"id": "with-q", "name": WITH_QUERY_NAME,
         "ma_top3": [{"pmid": "22222222", "title": "Old", "year": 2020}]},
    ])


# ─────────────────────────────── QA-P1-2 ───────────────────────────────


def test_no_query_preserves(harness):
    """Карточка без запроса в SUPPLEMENTS сохраняет свой ma_top3 (DATA-P1-1)."""
    seed(harness["path"])
    bks.main()
    cards = load(harness["path"])
    assert card(cards, NO_QUERY_NAME)["ma_top3"] == [
        {"pmid": "11111111", "title": "Kept", "year": 2024}
    ]


def test_network_failure_preserves(harness):
    """Обрыв сети не обнуляет ma_top3 у карточек с запросом (ветка except)."""
    seed(harness["path"])
    harness["fail_network"]()
    bks.main()
    cards = load(harness["path"])
    assert card(cards, WITH_QUERY_NAME)["ma_top3"] == [
        {"pmid": "22222222", "title": "Old", "year": 2020}
    ]
    assert card(cards, NO_QUERY_NAME)["ma_top3"] == [
        {"pmid": "11111111", "title": "Kept", "year": 2024}
    ]


def test_idempotent(harness):
    """Два прогона подряд → байт-в-байт одинаковый data.json."""
    seed(harness["path"])
    bks.main()
    first = harness["path"].read_text(encoding="utf-8")
    bks.main()
    second = harness["path"].read_text(encoding="utf-8")
    assert first == second
    # Сеть вызвана один раз на прогон (карточка с запросом ровно одна):
    # 2 прогона → 2 вызова. Больше — значит обход пошёл по карточкам без query.
    assert harness["state"]["calls"] == 2


def test_query_card_refreshes(harness):
    """Карточка с запросом ma_top3 обновляет, а не сохраняет старое."""
    seed(harness["path"])
    bks.main()
    cards = load(harness["path"])
    assert card(cards, WITH_QUERY_NAME)["ma_top3"] == NEW_ENTRY


def test_no_data_loss_live_data(harness):
    """165 PMID карточек без запрося переживают прогон на живых данных.

    Читает настоящий docs/data.json (read-only), гоняет main() на его копии
    и сверяет множества PMID. Регрессия DATA-P1-1 сразу видна числом.
    """
    live = ROOT / "docs" / "data.json"
    if not live.exists():
        pytest.skip("docs/data.json отсутствует")
    original = json.loads(live.read_text(encoding="utf-8"))

    write_cards(harness["path"], original)
    bks.main()
    after = load(harness["path"])

    before_pmids = {
        s["id"]: {e["pmid"] for e in (s.get("ma_top3") or [])}
        for s in original
        if not SUPPLEMENTS.get(s["name"])
    }
    after_pmids = {
        s["id"]: {e["pmid"] for e in (s.get("ma_top3") or [])}
        for s in after
        if not SUPPLEMENTS.get(s["name"])
    }
    assert before_pmids, "в данных нет карточек без запроса — тест потерял смысл"
    assert before_pmids == after_pmids

    total_before = sum(len(s.get("ma_top3") or []) for s in original
                       if not SUPPLEMENTS.get(s["name"]))
    assert total_before == sum(len(v) for v in after_pmids.values())