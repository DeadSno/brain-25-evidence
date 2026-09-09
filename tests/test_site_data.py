import json
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"


def test_files_present():
    for f in ["index.html", "map.html", "style.css", "script.js", "data.json"]:
        assert (DOCS / f).exists(), f"нет файла docs/{f}"


def test_data_json_valid():
    data = json.loads((DOCS / "data.json").read_text(encoding="utf-8"))
    assert len(data) >= 41, f"ожидали 41+ добавок, получили {len(data)}"


def test_required_fields():
    data = json.loads((DOCS / "data.json").read_text(encoding="utf-8"))
    req = {"id", "name", "code", "verdict", "category",
           "scienceIndex", "metaCount", "effects"}
    for d in data:
        missing = req - set(d)
        assert not missing, f"{d.get('name')}: не хватает полей {missing}"
        assert d["code"] in (1, 0, -1), f"{d['name']}: странный вердикт {d['code']}"