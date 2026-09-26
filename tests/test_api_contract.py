"""Тесты соответствия API OpenAPI-спеке."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "docs" / "api" / "v1"


def test_api_dir_exists():
    assert API.exists(), f"{API} не найден"


def test_index_json_exists():
    assert (API / "index.json").exists(), "index.json не найден"


def test_supplements_json_exists():
    assert (API / "supplements.json").exists(), "supplements.json не найден"


def test_openapi_exists():
    assert (API / "openapi.yaml").exists(), "openapi.yaml не найден"


def test_postman_collection_exists():
    assert (API / "postman_collection.json").exists(), "postman_collection.json не найден"


def test_index_structure():
    idx = json.loads((API / "index.json").read_text(encoding="utf-8"))
    for f in ["version", "count", "stats", "ids"]:
        assert f in idx, f"index.json без {f}"
    assert idx["count"] == 130
    assert len(idx["ids"]) == 130


def test_supplements_structure():
    d = json.loads((API / "supplements.json").read_text(encoding="utf-8"))
    assert "supplements" in d
    assert len(d["supplements"]) == 130
    for s in d["supplements"]:
        for f in ["id", "grade"]:
            assert f in s, f"supplement без {f}"


def test_grades_in_index():
    idx = json.loads((API / "index.json").read_text(encoding="utf-8"))
    grades = idx["stats"]["grades"]
    total = sum(grades.values())
    assert total == 130, f"Сумма grades={total}, ожидалось 130"
