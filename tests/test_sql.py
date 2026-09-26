"""Тесты SQL-запросов на DuckDB.

Проверяет что queries.sql выполняется, возвращает данные,
и основные инварианты БД соблюдены.

Skip если duckdb не установлена или БД не создана.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "db" / "brain.duckdb"

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="DuckDB не создана. Запусти python scripts/db/import_to_duckdb.py"
)


@pytest.fixture(scope="module")
def db():
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    yield con
    con.close()


def test_supplement_count(db):
    n = db.execute("SELECT COUNT(*) FROM supplement").fetchone()[0]
    assert n == 130, f"Ожидалось 130 добавок, есть {n}"


def test_all_grades_valid(db):
    rows = db.execute("SELECT DISTINCT grade FROM supplement").fetchall()
    grades = {r[0] for r in rows}
    assert grades <= {"A", "B", "C", "D"}, f"Невалидные grades: {grades}"


def test_mech_count(db):
    n = db.execute("SELECT COUNT(*) FROM mech").fetchone()[0]
    assert n > 200, f"Мало мех: {n}"


def test_interaction_severity(db):
    rows = db.execute("SELECT DISTINCT severity FROM interaction").fetchall()
    sevs = {r[0] for r in rows}
    valid = {"low", "medium", "high", "critical"}
    assert sevs <= valid, f"Невалидные severity: {sevs - valid}"


def test_supplement_has_key_sources(db):
    n = db.execute("""
        SELECT COUNT(*) FROM supplement s
        WHERE NOT EXISTS (SELECT 1 FROM key_source ks WHERE ks.supplement_id = s.id)
    """).fetchone()[0]
    assert n == 0, f"{n} добавок без key_sources"


def test_effect_tags_18(db):
    n = db.execute("SELECT COUNT(*) FROM effect_tag").fetchone()[0]
    assert n == 18, f"Ожидалось 18 тегов, есть {n}"


def test_top_science_index(db):
    rows = db.execute("""
        SELECT id, science_index FROM supplement
        WHERE science_index IS NOT NULL
        ORDER BY science_index DESC LIMIT 1
    """).fetchall()
    assert len(rows) == 1
    assert rows[0][1] > 5000, f"Топ SI={rows[0][1]}, ожидалось >5000"
