"""Интеграционный тест: API ↔ DuckDB согласованы.

Проверяет что данные в публичном API (docs/api/v1/*.json)
соответствуют данным в аналитической БД (data/db/brain.duckdb).

Это связывает два слоя: публичный API и внутреннюю аналитику.

Skip если duckdb не установлен или БД не создана.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "docs" / "api" / "v1"
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


@pytest.fixture(scope="module")
def api_data():
    idx = json.loads((API / "index.json").read_text(encoding="utf-8"))
    sup = json.loads((API / "supplements.json").read_text(encoding="utf-8"))
    return {"index": idx, "supplements": sup}


def test_count_matches_between_api_and_db(db, api_data):
    """Количество карточек в API = количеству в DuckDB."""
    api_count = api_data["index"]["count"]
    db_count = db.execute("SELECT COUNT(*) FROM supplement").fetchone()[0]
    assert api_count == db_count, f"API={api_count}, DB={db_count}"


def test_all_api_ids_exist_in_db(db, api_data):
    """Все ID из API есть в таблице supplement."""
    api_ids = set(api_data["index"]["ids"])
    db_ids = {r[0] for r in db.execute("SELECT id FROM supplement").fetchall()}
    missing = api_ids - db_ids
    assert not missing, f"IDs в API, но не в DB: {missing}"


def test_all_db_ids_exist_in_api(db, api_data):
    """Все ID из DuckDB есть в API."""
    api_ids = set(api_data["index"]["ids"])
    db_ids = {r[0] for r in db.execute("SELECT id FROM supplement").fetchall()}
    missing = db_ids - api_ids
    assert not missing, f"IDs в DB, но не в API: {missing}"


def test_grades_match_between_api_and_db(db, api_data):
    """Распределение грейдов в API = в DB."""
    api_grades = api_data["index"]["stats"]["grades"]
    db_rows = db.execute("""
        SELECT grade, COUNT(*) FROM supplement GROUP BY grade
    """).fetchall()
    db_grades = {r[0]: r[1] for r in db_rows}
    assert api_grades == db_grades, f"API={api_grades}, DB={db_grades}"


def test_science_index_consistency(db, api_data):
    """scienceIndex совпадает для топ-5 добавок."""
    top_api = sorted(
        [s for s in api_data["supplements"]["supplements"] if s.get("scienceIndex")],
        key=lambda x: -x["scienceIndex"]
    )[:5]
    top_db = db.execute("""
        SELECT id, science_index FROM supplement
        WHERE science_index IS NOT NULL
        ORDER BY science_index DESC LIMIT 5
    """).fetchall()
    for api_card, (db_id, db_si) in zip(top_api, top_db):
        assert api_card["id"] == db_id, f"Порядок отличается: {api_card['id']} vs {db_id}"
        assert api_card["scienceIndex"] == db_si, f"{db_id}: API={api_card['scienceIndex']}, DB={db_si}"


def test_effect_tags_count_consistent(db):
    """18 тегов в DB — совпадает с docs/effect_tags.json."""
    tags_file = ROOT / "docs" / "effect_tags.json"
    tags = json.loads(tags_file.read_text(encoding="utf-8"))
    unique_tags = set()
    for v in tags.values():
        unique_tags.update(v)
    db_tags = db.execute("SELECT COUNT(DISTINCT tag) FROM effect_tag").fetchone()[0]
    assert db_tags == len(unique_tags), f"API={len(unique_tags)}, DB={db_tags}"
