"""Контракт docs/data.json: схема карточек, формат key_sources, синхронизация с кодом."""
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def data(data_json_path: Path) -> list[dict]:
    return json.loads(data_json_path.read_text(encoding="utf-8"))


def test_data_json_parses(data: list[dict]) -> None:
    assert isinstance(data, list)
    assert len(data) > 0


def test_every_card_has_id(data: list[dict]) -> None:
    for c in data:
        assert c.get("id"), f"карточка без id: {c}"


def test_ids_unique(data: list[dict]) -> None:
    ids = [c["id"] for c in data]
    dups = sorted({x for x in ids if ids.count(x) > 1})
    assert not dups, f"дубли id: {dups}"


def test_every_card_has_grade(data: list[dict]) -> None:
    for c in data:
        assert c.get("grade") in {"A", "B", "C", "D"}, \
            f"{c['id']}: неверный grade {c.get('grade')!r}"


def test_every_card_has_verdict(data: list[dict]) -> None:
    valid = {"работает", "зависит от контекста", "не подтверждено"}
    for c in data:
        assert c.get("verdict") in valid, \
            f"{c['id']}: неверный verdict {c.get('verdict')!r}"


def test_key_sources_format(data: list[dict]) -> None:
    """key_sources = list[dict], у каждого pmid/title/year/journal."""
    for c in data:
        for s in c.get("key_sources") or []:
            assert isinstance(s, dict), f"{c['id']}: элемент key_sources не dict"
            assert s.get("pmid"), f"{c['id']}: пустой pmid"
            assert str(s["pmid"]).isdigit(), f"{c['id']}: нечисловой pmid {s['pmid']!r}"
            assert s.get("title"), f"{c['id']}: пустой title для {s['pmid']}"
            assert s.get("year", 0) >= 1900, f"{c['id']}: плохой year для {s['pmid']}"
            assert s.get("journal"), f"{c['id']}: пустой journal для {s['pmid']}"


def test_no_duplicate_pmids_within_card(data: list[dict]) -> None:
    for c in data:
        pmids = [s["pmid"] for s in c.get("key_sources") or []]
        dups = [p for p in set(pmids) if pmids.count(p) > 1]
        assert not dups, f"{c['id']}: дубли PMID {dups}"


def test_curated_pmids_match_data_json(data: list[dict]) -> None:
    """MANUAL_PMIDS из search_sources.py должен совпадать с data.json.

    Ловит рассинхрон вроде B12: обновили MANUAL_PMIDS, но забыли apply_sources.
    """
    from scripts.search_sources import MANUAL_PMIDS

    by_id = {c["id"]: c for c in data}
    for cid, expected in MANUAL_PMIDS.items():
        assert cid in by_id, f"{cid}: нет карточки в data.json"
        actual = [s["pmid"] for s in by_id[cid].get("key_sources") or []]
        assert actual == expected, (
            f"{cid}: data.json {actual} != MANUAL_PMIDS {expected}. "
            f"Запустите: search_sources.py --all-missing && apply_sources.py --apply"
        )
