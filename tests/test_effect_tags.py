"""онтракт effect_tags.json и effect_tags_map.py."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data() -> list[dict]:
    return json.loads((ROOT / "docs/data.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def effect_tags() -> dict[str, list[str]]:
    return json.loads((ROOT / "docs/effect_tags.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tag_map():
    from scripts.effect_tags_map import TAGS, TAG_LABELS
    return TAGS, TAG_LABELS


def test_effect_tags_json_exists():
    assert (ROOT / "docs/effect_tags.json").exists(), \
        "апустите: python scripts/build_effect_tags.py"


def test_all_cards_have_tags(data, effect_tags):
    for c in data:
        assert c["id"] in effect_tags, f"{c['id']}: нет в effect_tags.json"
        assert effect_tags[c["id"]], f"{c['id']}: пустой список тегов"


def test_no_extra_ids(effect_tags, data):
    ids = {c["id"] for c in data}
    extra = set(effect_tags.keys()) - ids
    assert not extra, f"лишние id в effect_tags.json: {extra}"


def test_tags_are_known(effect_tags, tag_map):
    _, known = tag_map
    for cid, tags in effect_tags.items():
        for t in tags:
            assert t in known, f"{cid}: неизвестный тег {t!r}"


def test_tags_sorted(effect_tags):
    keys = list(effect_tags.keys())
    assert keys == sorted(keys), "ключи должны быть отсортированы"


def test_map_matches_json(effect_tags, tag_map):
    tags_map, _ = tag_map
    assert {k: v for k, v in sorted(tags_map.items())} == effect_tags, \
        "effect_tags.json рассинхронизирован с effect_tags_map.py — запустите build_effect_tags.py"
