"""Проверка целостности data_en.json и отдельных файлов data_en/<id>.json (QA-08, FIX-74).

Тесты
-----
1. data_en.json и все 130 файла data_en/<id>.json существуют.
2. Ключи внутри data_en/<id>.json — подмножество ключей data.json (нельзя
   вводить новые ключи в английскую версию, которых нет в исходнике).
3. len(data_en.json['supplements']) == 130.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA_EN = DOCS / "data_en.json"
DATA_EN_DIR = DOCS / "data_en"
DATA_JSON = DOCS / "data.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_data_en_files_exist() -> None:
    """data_en.json и все 130 файла data_en/<id>.json существуют."""
    assert DATA_EN.is_file(), "docs/data_en.json не найден"
    files = sorted(DATA_EN_DIR.glob("*.json"))
    assert len(files) == 130, f"ожидалось 130 файлов в data_en/, найдено {len(files)}"
    for path in files:
        assert path.is_file(), f"файл не найден: {path}"


def test_data_en_structure_matches_data_json() -> None:
    """Ключи внутри data_en/<id>.json — подмножество ключей data.json."""
    data = _load(DATA_JSON)
    data_keys: set[str] = set()
    for item in data:
        data_keys.update(item.keys())

    data_en = _load(DATA_EN)
    assert "supplements" in data_en, "в data_en.json нет ключа 'supplements'"

    files = sorted(DATA_EN_DIR.glob("*.json"))
    for path in files:
        content = _load(path)
        assert "supplements" in content, f"в {path.name} нет ключа 'supplements'"
        for sid, supp in content["supplements"].items():
            supp_keys = set(supp.keys())
            extra = supp_keys - data_keys
            assert not extra, (
                f"в {path.name} supplements[{sid!r}] есть ключи, "
                f"отсутствующие в data.json: {sorted(extra)}"
            )


def test_data_en_supplements_count() -> None:
    """В data_en.json ровно 130 аддитивов."""
    data_en = _load(DATA_EN)
    assert len(data_en["supplements"]) == 130, (
        f"ожидалось 130 аддитивов, найдено {len(data_en['supplements'])}"
    )
