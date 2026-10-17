"""DATA-P2-16: tests/test_fetch_hedges_g.py

Регрессия: `scripts/fetch_hedges_g.py` писал `docs/hedges_g_all.json` из
словаря `all_cands`, но ветки `errors` и `no_term` делали `continue` ДО строки,
которая заполняет `all_cands[cid]`. Карточка с сетевой ошибкой целиком
выпадала из файла — вместе с уже накопленными по ней кандидатами.

15.10.2026 это стоило нам ключа «Мелатонин»: один `ConnectionResetError 10054`
стёр 8 заполненных записей из 130 ключей. Тот же дефект у ветки `no_term`
(в этом прогоне она не сработала, `no_term = 0`).

Что и почему проверяется:

  * `test_key_survives_network_error` — карточка, на которой сеть упала,
    обязана остаться в файле. Раньше исчезала целиком.
  * `test_key_survives_empty_candidates` — карточка без кандидатов остаётся
    в файле со значением `[]`, а не выпадает.
  * `test_key_survives_missing_term` — карточка без запроса в
    `data_pubmed_terms.json` остаётся в файле со значением `[]`.
  * `test_ok_card_gets_its_candidates` — обычная карточка получает ровно
    своих кандидатов. Страховка от «тест проходит, потому что всё пусто».
  * `test_every_card_present_regardless_of_outcome` — смешанный прогон, где
    каждая карточка падает своим способом: ключ обязан быть у ВСЕХ, а
    заполнены только «ok».
  * `test_report_statuses_still_distinguish_failure_from_absence` — баг был
    не только в файле: отчёт обязан по-прежнему отличать `error` (сеть) от
    `no_candidates` (PubMed пуст). Иначе после починки файла потеряется
    единственный сигнал, что прогон был неполным.

Сеть не используется: `extract_g.candidates` подменяется заглушкой, все пути
уводятся в tmp_path, живой репозиторий тест не трогает. Реальный прогон с
NCBI занимает ~50 минут на 130 карточек — в тест он не годится.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import extract_g, fetch_hedges_g  # noqa: E402

# Карточки с разными исходами. Термы нужны не всем: у «БезТерма» их нет.
CARDS = [
    {"id": "Ок", "name": "Ок"},
    {"id": "Сеть", "name": "Сеть"},
    {"id": "Пусто", "name": "Пусто"},
    {"id": "БезТерма", "name": "БезТерма"},
]
TERMS = {
    "Ок": "ok supplement AND (meta-analysis[pt])",
    "Сеть": "flaky supplement AND (meta-analysis[pt])",
    "Пусто": "obscure supplement AND (meta-analysis[pt])",
}
OK_CANDIDATES = [{"pmid": "11111111", "g": -0.5, "ci": [-0.9, -0.1], "outcome": None}]


@pytest.fixture()
def run_script(tmp_path, monkeypatch):
    """Run fetch_hedges_g.main() against tmp files and a stubbed network layer.

    Returns a callable taking the candidates stub; it yields the parsed
    hedges_g_all.json plus the parsed report.
    """
    data_path = tmp_path / "data.json"
    terms_path = tmp_path / "terms.json"
    all_path = tmp_path / "hedges_g_all.json"
    report_path = tmp_path / "reports" / "hedges_g_report.json"

    data_path.write_text(json.dumps(CARDS, ensure_ascii=False), encoding="utf-8")
    terms_path.write_text(json.dumps(TERMS, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(fetch_hedges_g, "DATA_JSON", data_path)
    monkeypatch.setattr(fetch_hedges_g, "TERMS_JSON", terms_path)
    monkeypatch.setattr(fetch_hedges_g, "ALL_JSON", all_path)
    monkeypatch.setattr(fetch_hedges_g, "REPORT", report_path)
    monkeypatch.setattr(sys, "argv", ["fetch_hedges_g.py"])

    def _run(candidates):
        monkeypatch.setattr(extract_g, "candidates", candidates)
        assert fetch_hedges_g.main() == 0
        return (
            json.loads(all_path.read_text(encoding="utf-8")),
            json.loads(report_path.read_text(encoding="utf-8")),
        )

    return _run


def _stub(results):
    """Build a candidates() stub backed by a {card_id: value_or_exception} map."""

    def candidates(cid, base):
        value = results[cid]
        if isinstance(value, Exception):
            raise value
        return value

    return candidates


def test_key_survives_network_error(run_script):
    """A card that hit a network error must keep its key, not vanish."""
    connection_reset = ConnectionResetError(10054, "connection reset by peer")
    all_cands, report = run_script(
        _stub(
            {
                "Ок": OK_CANDIDATES,
                "Сеть": connection_reset,
                "Пусто": [],
                "БезТерма": [],
            }
        )
    )

    assert "Сеть" in all_cands, (
        "карточка с сетевой ошибкой выпала из hedges_g_all.json — "
        "баг DATA-P2-16 вернулся"
    )
    assert all_cands["Сеть"] == []
    assert report["cards"]["Сеть"]["status"] == "error"
    assert report["totals"]["error"] == 1


def test_key_survives_empty_candidates(run_script):
    """A card with no candidates keeps an empty list instead of disappearing."""
    all_cands, report = run_script(
        _stub({"Ок": OK_CANDIDATES, "Сеть": [], "Пусто": [], "БезТерма": []})
    )

    assert "Пусто" in all_cands
    assert all_cands["Пусто"] == []
    assert report["cards"]["Пусто"]["status"] == "no_candidates"


def test_key_survives_missing_term(run_script):
    """A card with no PubMed term keeps its key too (same continue-before-write)."""
    all_cands, report = run_script(
        _stub({"Ок": OK_CANDIDATES, "Сеть": [], "Пусто": [], "БезТерма": []})
    )

    assert "БезТерма" in all_cands, "ветка no_term выкидывает карточку из файла"
    assert all_cands["БезТерма"] == []
    assert report["cards"]["БезТерма"]["status"] == "no_term"


def test_ok_card_gets_its_candidates(run_script):
    """Guard against a green suite that only proves everything stayed empty."""
    all_cands, report = run_script(
        _stub({"Ок": OK_CANDIDATES, "Сеть": [], "Пусто": [], "БезТерма": []})
    )

    assert [c["pmid"] for c in all_cands["Ок"]] == ["11111111"]
    assert report["cards"]["Ок"]["status"] == "ok"
    assert report["totals"]["found"] == 1


def test_every_card_present_regardless_of_outcome(run_script):
    """One card per failure mode: every card must appear in the output file."""
    all_cands, report = run_script(
        _stub(
            {
                "Ок": OK_CANDIDATES,
                "Сеть": TimeoutError("timed out"),
                "Пусто": [],
                "БезТерма": [],
            }
        )
    )

    assert set(all_cands) == {"Ок", "Сеть", "Пусто", "БезТерма"}, (
        f"в файле {sorted(all_cands)}, а карточек было {len(CARDS)}"
    )
    assert len(all_cands) == len(CARDS)
    filled = [k for k, v in all_cands.items() if v]
    assert filled == ["Ок"], f"заполнены должны быть только успешные, а заполнено {filled}"


def test_report_statuses_still_distinguish_failure_from_absence(run_script):
    """The file fix must not flatten error and no_term into one bucket."""
    all_cands, report = run_script(
        _stub(
            {
                "Ок": OK_CANDIDATES,
                "Сеть": ConnectionResetError(10054, "reset"),
                "Пусто": [],
                "БезТерма": [],
            }
        )
    )

    statuses = {cid: card["status"] for cid, card in report["cards"].items()}
    assert statuses == {
        "Ок": "ok",
        "Сеть": "error",
        "Пусто": "no_candidates",
        "БезТерма": "no_term",
    }, (
        "после починки файла отчёт обязан по-прежнему различать сетевой сбой "
        "и отсутствие данных в PubMed — иначе прогон снова станет неотличим "
        "от полного"
    )
    assert report["totals"] == {
        "found": 1,
        "with_ci": 1,
        # Обе ветки — «Пусто» (кандидаты есть, g в abstract нет) и «БезТерма»
        # (запроса нет вовсе) — инкрементят один и тот же счётчик.
        "no_candidates": 2,
        "error": 1,
        "reused_shared": 0,
    }