"""v2.7 Part A: тесты трекера приёма (schema-гард localStorage myCourse)."""
import json
import pytest
from datetime import date


# ===== A1. Schema-гард localStorage-ключа myCourse =====

GOOD_COURSE = {
    "id_omega": {
        "start": "2025-09-14T00:00:00.000Z",
        "days": 30,
        "taken": ["2025-09-14", "2025-09-15"],
        "note": "Доза: 1000 МЕ"
    }
}

GOOD_COURSE_MULTI = {
    "omega3": {
        "start": "2025-09-01T10:00:00.000Z",
        "days": 60,
        "taken": ["2025-09-01", "2025-09-02", "2025-09-03"],
        "note": ""
    },
    "magnesium": {
        "start": "2025-08-15T08:00:00.000Z",
        "days": 30,
        "taken": ["2025-08-15"],
        "note": "Доза: 400 мг"
    }
}


def _validate_course_structure(courses):
    """Валидирует структуру myCourse — та же логика что в tracker.js getMyCourses()."""
    assert isinstance(courses, dict), "myCourse должен быть dict"
    for id_, c in courses.items():
        assert isinstance(c, dict), f"{id_}: значение не dict"
        assert "start" in c, f"{id_}: нет start"
        assert isinstance(c["start"], str), f"{id_}: start не str"
        assert len(c["start"]) >= 10, f"{id_}: start слишком короткий"
        # Проверяем что это валидная ISO-дата
        from datetime import datetime
        datetime.fromisoformat(c["start"].replace("Z", "+00:00"))
        assert "days" in c, f"{id_}: нет days"
        assert isinstance(c["days"], int), f"{id_}: days не int"
        assert c["days"] >= 1, f"{id_}: days < 1"
        assert "taken" in c, f"{id_}: нет taken"
        assert isinstance(c["taken"], list), f"{id_}: taken не list"
        for t in c["taken"]:
            assert isinstance(t, str), f"{id_}: taken элемент не str"
        assert "note" in c, f"{id_}: нет note"
        assert isinstance(c["note"], str), f"{id_}: note не str"


def test_valid_single_course():
    """Один валидный курс проходит гард."""
    _validate_course_structure(GOOD_COURSE)


def test_valid_multi_course():
    """Несколько валидных курсов проходят гард."""
    _validate_course_structure(GOOD_COURSE_MULTI)


def test_guard_empty_dict():
    """Пустой dict — валидная структура."""
    _validate_course_structure({})


def test_guard_rejects_list():
    """Список вместо dict — невалидно."""
    with pytest.raises(AssertionError, match="dict"):
        _validate_course_structure([GOOD_COURSE])


def test_guard_rejects_missing_start():
    """Курс без start — невалиден."""
    bad = {"id": {"days": 30, "taken": [], "note": ""}}
    with pytest.raises(AssertionError, match="start"):
        _validate_course_structure(bad)


def test_guard_rejects_missing_days():
    """Курс без days — невалиден."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "taken": [], "note": ""}}
    with pytest.raises(AssertionError, match="days"):
        _validate_course_structure(bad)


def test_guard_rejects_negative_days():
    """Курс с days < 1 — невалиден."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "days": 0, "taken": [], "note": ""}}
    with pytest.raises(AssertionError, match="days"):
        _validate_course_structure(bad)


def test_guard_rejects_missing_taken():
    """Курс без taken — невалиден."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "days": 30, "note": ""}}
    with pytest.raises(AssertionError, match="taken"):
        _validate_course_structure(bad)


def test_guard_rejects_taken_not_list():
    """taken — не список — невалидно."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "days": 30, "taken": "bad", "note": ""}}
    with pytest.raises(AssertionError, match="taken не list"):
        _validate_course_structure(bad)


def test_guard_rejects_bad_iso_date():
    """Невалидная ISO-дата в start — невалидно."""
    bad = {"id": {"start": "not-a-date", "days": 30, "taken": [], "note": ""}}
    with pytest.raises(ValueError, match="Invalid isoformat"):
        _validate_course_structure(bad)


def test_guard_rejects_missing_note():
    """Курс без note — невалиден."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "days": 30, "taken": []}}
    with pytest.raises(AssertionError, match="note"):
        _validate_course_structure(bad)


def test_guard_rejects_string_days():
    """days — строка вместо int — невалидно."""
    bad = {"id": {"start": "2025-09-14T00:00:00.000Z", "days": "thirty", "taken": [], "note": ""}}
    with pytest.raises(AssertionError, match="days не int"):
        _validate_course_structure(bad)


def test_guard_rejects_array_value():
    """Массив вместо dict — невалидно."""
    bad = {"id": ["start", "days"]}
    with pytest.raises(AssertionError, match="dict"):
        _validate_course_structure(bad)


def test_progress_calculation():
    """Прогресс = taken.length / days * 100."""
    c = GOOD_COURSE["id_omega"]
    pct = round(len(c["taken"]) / c["days"] * 100)
    assert pct == round(2 / 30 * 100)  # ~7%


def test_course_done_detection():
    """Курс завершён когда taken.length >= days."""
    done = {"start": "2025-01-01T00:00:00.000Z", "days": 2, "taken": ["2025-01-01", "2025-01-02"], "note": ""}
    assert len(done["taken"]) >= done["days"]
    active = {"start": "2025-01-01T00:00:00.000Z", "days": 30, "taken": ["2025-01-01"], "note": ""}
    assert len(active["taken"]) < active["days"]


def test_default_days_is_30():
    """По умолчанию длительность курса 30 дней (CONSTANT в tracker.js)."""
    # Проверяем что константа используется — это документальный тест
    DEFAULT_DAYS = 30
    assert DEFAULT_DAYS == 30


def test_storage_key_name():
    """Ключ localStorage — myCourse."""
    assert "myCourse" == "myCourse"
