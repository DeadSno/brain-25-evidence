"""QA-P2-04 — parse_xml_meta.py не падал на пустом разборе.

До фикса статистика делила на n = len(out) без проверки. Файл OUT к этому
моменту уже записан, то есть на любом битом/пустом входе данные сохранялись,
а скрипт ронялся на последней строке и код возврата становился не 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import parse_xml_meta  # noqa: E402


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """Пустой каталог входа + выход во временную папку."""
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    out = tmp_path / "processed" / "xml_meta.json"
    monkeypatch.setattr(parse_xml_meta, "TEXT_DIR", text_dir)
    monkeypatch.setattr(parse_xml_meta, "OUT", out)
    return text_dir, out


def test_empty_input_does_not_crash(sandbox, capsys):
    """Ноль разобранных файлов — не ZeroDivisionError, а код возврата 0."""
    assert parse_xml_meta.main() == 0
    out = capsys.readouterr().out
    assert "Всего:        0" in out
    assert "n/a" in out
    assert "%" not in out.split("С funding:")[1]


def test_empty_input_still_writes_output(sandbox):
    """Файл результата создаётся и на пустом входе — как и до фикса."""
    parse_xml_meta.main()
    _, out = sandbox
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8")) == {}


def test_unparseable_files_are_skipped_not_fatal(sandbox):
    """Нечитаемый XML даёт out == {} — тот же путь, что и пустой каталог."""
    text_dir, out = sandbox
    (text_dir / "broken.xml").write_text("<article><unclosed>", encoding="utf-8")
    assert parse_xml_meta.main() == 0
    assert json.loads(out.read_text(encoding="utf-8")) == {}