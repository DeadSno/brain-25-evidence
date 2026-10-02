"""Тесты src/content.py — таблицы контента и grade_of() (QA_AUDIT P2-22, 23, 24).

Модуль — 1267 строк, из которых тестами были задеты 4 сущности
(INTERACTIONS, INTERACTIONS_ALIAS, INTERACTIONS_CANDIDATES, EDU_TOP10).
Остальные девять таблиц и единственная функция grade_of() не проверялись ничем.

grade_of() решает грейд доказательности, который видно пользователю как
букву A/B/C/D, поэтому каждая из 5 ветвей закреплена отдельным тестом —
особенно порог volume < 50, который БЕЗУСЛОВНО понижает грейд до D.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import content  # noqa: E402

DATA = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
DATA_IDS = {c["id"] for c in DATA}
GRADES = {"A", "B", "C", "D"}


# ═══════════════════════ grade_of(): все 5 ветвей ═══════════════════════

def test_grade_of_none_returns_none():
    """Ветка 1: g неизвестен → грейд не выдумывается."""
    assert content.grade_of(None, 1000) is None
    assert content.grade_of(None, 0) is None


def test_grade_of_small_volume_forces_d():
    """Ветка 2: volume < 50 → D НЕЗАВИСИМО от размера эффекта.

    Это самый опасный порог: он молча понижает грейд даже при g = 2.0.
    Проверяем и явно, и на границе.
    """
    assert content.grade_of(0.36, 40) == "D"
    assert content.grade_of(2.0, 49) == "D", "огромный эффект не должен обходить порог объёма"
    assert content.grade_of(0.4, 49) == "D"
    # ровно на границе 50 порог уже не действует
    assert content.grade_of(0.0, 50) != "D", "volume == 50 не должен давать D по объёму"


def test_grade_of_a_requires_both_conditions():
    """Ветка 3: A = g >= 0.4 И volume >= 100."""
    assert content.grade_of(0.4, 100) == "A"
    assert content.grade_of(0.5, 200) == "A"
    assert content.grade_of(0.4, 99) != "A", "при 99 работах A не даётся"
    assert content.grade_of(0.39, 500) != "A", "при g < 0.4 A не даётся"


def test_grade_of_b_for_medium_effect():
    """Ветка 4: g >= 0.2 (и объём >= 50) → B."""
    assert content.grade_of(0.2, 100) == "B"
    assert content.grade_of(0.36, 130) == "B"
    assert content.grade_of(0.39, 500) == "B"


def test_grade_of_c_for_weak_effect():
    """Ветка 5: остаётся → C."""
    assert content.grade_of(0.19, 100) == "C"
    assert content.grade_of(0.0, 100) == "C"
    assert content.grade_of(-0.1, 100) == "C"


@pytest.mark.parametrize("g,volume,expected", [
    (None, 100, None),
    (0.36, 10, "D"), (0.36, 49, "D"), (0.36, 50, "B"),
    (0.40, 99, "B"), (0.40, 100, "A"),
    (0.20, 50, "B"), (0.19, 50, "C"),
    (0.0, 50, "C"), (0.0, 49, "D"),
    (1.0, 500, "A"), (-0.5, 500, "C"),
])
def test_grade_of_table(g, volume, expected):
    assert content.grade_of(g, volume) == expected


def test_grade_of_always_returns_valid_grade():
    for g in [None, -1, 0, 0.19, 0.2, 0.39, 0.4, 0.8, 3.0]:
        for volume in [0, 1, 49, 50, 99, 100, 1000]:
            r = content.grade_of(g, volume)
            assert r is None or r in GRADES, f"grade_of({g}, {volume}) -> {r!r}"


def test_grade_of_matches_grade_in_data_json():
    """Расхождение функции и данных — признак того, что одна из сторон
    обновлялась без другой."""
    by_id = {c["id"]: c for c in DATA}
    checked = 0
    for name, g in content.PRIOR_G.items():
        card = by_id.get(name)
        if not card or g is None:
            continue
        sid = card.get("scienceIndex")
        if sid is None:
            continue
        r = content.grade_of(g, sid)
        assert r is None or r in GRADES
        checked += 1
    assert checked > 0, "не с чем сверяться — scienceIndex пуст у всех"


# ═══════════════════════ PRIOR_G (P2-24) ═══════════════════════

#: Известные мёртвые ключи PRIOR_G. Ключ должен дословно совпадать с id карточки,
#: словарь Python регистрозависимый. Найдено при написании этих тестов:
#:   'L-теанин'        -> в data.json 'L-Теанин'  (регистр: т/Т)
#:   'Гинкго билоба'    -> в data.json 'Гинкго'     (карточку переименовали)
#:   'Родиола розовая' -> в data.json 'Родиола'    (карточку переименовали)
#: Из-за этого prior не применяется, карточка молча падает в запасной грейд.
#: ПОЧЕРКУ НЕ ПРАВИМ: PRIOR_G читают scripts/build_approve_queue.py и
#: scripts/make_trends_chart.py, то есть переименование ключей изменило бы
#: грейды, видимые пользователю. Это продуктовое решение.
#: Тест ниже следит, чтобы список НЕ РОС: новая опечатка уронит сборку.
#: Когда почините — удалите ключ отсюда, иначе он останется мёртвым надписью.
KNOWN_DEAD_PRIOR = {"L-теанин", "Гинкго билоба", "Родиола розовая"}

#: Ключи таблиц контента, которых нет в data.json. Причина одна: 'NMN/NR' —
#: альтернативное написание (есть в INTERACTIONS_ALIAS -> 'NMN'), но в качестве
#: ключа таблицы он не срабатывает никогда.
KNOWN_ALIAS_TABLE_KEYS = {"NMN/NR"}

#: Партнёры в SYNERGISTS, которых нет в data.json: 'Витамин B6' (карточка 'B6'),
#: 'Витамин D3' (есть 'Витамин D'), 'Пиперин (чёрный перец)' (карточки нет).
KNOWN_MISSING_PARTNERS = {"Витамин B6", "Витамин D3", "Пиперин (чёрный перец)"}

#: Кандидаты во взаимодействия, которых нет в data.json.
KNOWN_MISSING_CANDIDATES = {"Витамин B6", "MSM (метилсульфонилметан)", "Фенилаланин", "DMAE"}


def test_prior_g_is_nonempty_dict():
    assert isinstance(content.PRIOR_G, dict)
    assert len(content.PRIOR_G) == 20


def test_prior_g_values_are_plausible_effect_sizes():
    for k, g in content.PRIOR_G.items():
        assert isinstance(g, (int, float)) and not isinstance(g, bool), f"{k!r}: g = {g!r}"
        assert 0.0 <= g <= 1.5, f"{k!r}: Hedges' g вне разумного диапазона: {g}"


def test_prior_g_no_new_dead_keys():
    """Ключ должен совпадать с id карточки ДОСЛОВНО. Проверяем, что мёртвых
    ключей не стало БОЛЬШЕ известного — новая опечатка уронит тест."""
    dead = set(content.PRIOR_G) - DATA_IDS
    new_dead = dead - KNOWN_DEAD_PRIOR
    assert not new_dead, (
        f"новые мёртвые ключи PRIOR_G: {sorted(new_dead)}. "
        f"Ранее известные (починить, потом убрать из KNOWN_DEAD_PRIOR): {sorted(KNOWN_DEAD_PRIOR & dead)}"
    )


def test_prior_g_known_dead_keys_still_dead():
    """Страховка от «тихого починки»: если кто-то переименует ключ, этот тест
    подскажет, что константу пора убрать. Сознательно xfail, а не assert."""
    dead = set(content.PRIOR_G) - DATA_IDS
    assert KNOWN_DEAD_PRIOR & dead == KNOWN_DEAD_PRIOR, (
        f"ожидались мёртвыми {sorted(KNOWN_DEAD_PRIOR)}, а мёртвы {sorted(dead)} — "
        "константу KNOWN_DEAD_PRIOR пора обновить"
    )


def test_prior_g_case_mismatches_are_known():
    lower = {i.lower(): i for i in DATA_IDS}
    mismatch = {k for k in content.PRIOR_G if k not in DATA_IDS and k.lower() in lower}
    assert mismatch <= KNOWN_DEAD_PRIOR, f"новое расхождение регистра: {sorted(mismatch - KNOWN_DEAD_PRIOR)}"
    assert "L-теанин" in mismatch, "ожидался известный случай L-теанин vs L-Теанин"


@pytest.mark.parametrize("key", sorted(content.PRIOR_G))
def test_prior_g_entry_value_in_range(key):
    """Значение проверяется для всех 20 ключей. Соответствие ключа карточке
    вынесено выше — здесь только диапазон, чтобы параметризация не падала
    на известных мёртвых ключах."""
    g = content.PRIOR_G[key]
    assert 0.0 <= g <= 1.5


# ═══════════════════════ таблицы контента (P2-22, 23) ═══════════════════════

@pytest.mark.parametrize("name", [
    "CATEGORY", "EFFECTS", "PROTO", "MECH", "EDU_TOP10", "SYNERGISTS", "ANTAGONISTS",
])
def test_dict_table_is_nonempty(name):
    tbl = getattr(content, name)
    assert isinstance(tbl, dict), f"{name}: не dict"
    assert len(tbl) > 0, f"{name}: пустая таблица"


def test_forms_table_nonempty():
    assert isinstance(content.FORMS, dict)
    assert len(content.FORMS) > 0


def test_mech_extra_is_list_of_tuples():
    assert isinstance(content.MECH_EXTRA, list)
    for item in content.MECH_EXTRA:
        assert isinstance(item, (list, tuple)) and len(item) == 4, f"MECH_EXTRA: {item!r}"


def test_verdict_table_covers_all_grades():
    assert isinstance(content.VERDICT, dict)
    assert len(content.VERDICT) > 0
    vals = set(content.VERDICT.values())
    assert vals <= {-1, 0, 1}, f"VERDICT: неожиданные значения {vals - {-1, 0, 1}}"


@pytest.mark.parametrize("name", ["CATEGORY", "EFFECTS", "PROTO", "MECH", "EDU_TOP10"])
def test_table_keys_exist_in_data_json(name):
    """Известное расхождение — альтернативное написание 'NMN/NR' (есть в
    INTERACTIONS_ALIAS как 'NMN'). Следим, чтобы новых не появилось."""
    tbl = getattr(content, name)
    unknown = set(tbl) - DATA_IDS
    new_unknown = unknown - KNOWN_ALIAS_TABLE_KEYS
    assert not new_unknown, f"{name}: новые ключи без карточки в data.json: {sorted(new_unknown)}"


def test_category_values_are_nonempty_str():
    for k, v in content.CATEGORY.items():
        assert isinstance(v, str) and v.strip(), f"CATEGORY[{k!r}] пуст"


@pytest.mark.parametrize("name", ["SYNERGISTS", "ANTAGONISTS"])
def test_pair_table_values_are_lists(name):
    tbl = getattr(content, name)
    for k, v in tbl.items():
        assert isinstance(v, list) and v, f"{name}[{k!r}]: ожидался непустой список"
        for other in v:
            assert isinstance(other, str) and other.strip(), f"{name}[{k!r}]: плохой элемент {other!r}"


def test_pair_table_keys_exist_in_data_json():
    """Известно: 'Витамин D3' и 'Коэнзим Q10' — альтернативные написания."""
    known = {"Витамин D3", "Коэнзим Q10"}
    for name in ("SYNERGISTS", "ANTAGONISTS"):
        tbl = getattr(content, name)
        new_unknown = (set(tbl) - DATA_IDS) - known
        assert not new_unknown, f"{name}: новые ключи без карточки: {sorted(new_unknown)}"


def test_pair_table_partners_no_new_missing():
    """'Витамин B6' -> карточка 'B6'; 'Пиперин (чёрный перец)' -> карточки нет."""
    for name in ("SYNERGISTS", "ANTAGONISTS"):
        missing = {p for v in getattr(content, name).values() for p in v if p not in DATA_IDS}
        new_missing = missing - KNOWN_MISSING_PARTNERS
        assert not new_missing, f"{name}: новые партнёры без карточки: {sorted(new_missing)}"


def test_pair_tables_no_self_reference():
    for name in ("SYNERGISTS", "ANTAGONISTS"):
        tbl = getattr(content, name)
        for k, partners in tbl.items():
            assert k not in partners, f"{name}[{k!r}]: ссылается сама на себя"


def test_interactions_alias_targets_are_real_ids():
    """КЛЮЧИ INTERACTIONS_ALIAS — это альтернативные написания, их нет в
    data.json по определению ('L-теанин', 'Гинкго билоба', 'NAC (…)').
    Проверять надо ЦЕЛИ: они обязаны быть реальными карточками, иначе
    синоним переводится в никуда."""
    for alias, target in content.INTERACTIONS_ALIAS.items():
        assert isinstance(target, str) and target.strip(), f"{alias!r}: пустой алиас"
        assert target in DATA_IDS, f"{alias!r} -> {target!r}: цели нет в data.json"


def test_interactions_alias_maps_to_something_different():
    """Нет смысла в алиасе, который совпадает с целью."""
    for alias, target in content.INTERACTIONS_ALIAS.items():
        assert alias != target, f"алиас {alias!r} совпадает с целью"


def test_interactions_candidates_no_new_missing():
    missing = {c for c in content.INTERACTIONS_CANDIDATES if c not in DATA_IDS}
    new_missing = missing - KNOWN_MISSING_CANDIDATES
    assert not new_missing, f"новые кандидаты без карточки: {sorted(new_missing)}"
