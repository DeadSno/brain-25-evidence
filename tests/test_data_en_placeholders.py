"""Плейсхолдеры в `interactions` — DATA-04, FIX-50.

`interactions` — список вида `{"with": <добавка>, "severity": ..., "note": ...}`.
Поле `with` — ИМЯ добавки. До FIX-50 в 51 карточке там лежала строка-заглушка:
`"нет данных"` в `docs/data.json` и `"no data"` в `docs/data_en.json`
(перевод той же заглушки). Плейсхолдер в этом поле — ошибка уровня данных,
а не оформления: `docs/script.js:renderConflicts()` печатает `with`
безусловно, поэтому на карточке в модалке появлялась строка
«no data · низкая» — псевдо-взаимодействие с добавкой по имени «no data».

Фильтр `isNoData()` в `docs/hactar.js` (FIX-15) эту строку скрывал, но он
один: `script.min.js` про заглушку не знает и знать не должен. Поэтому
источник подчищен в данных, а `interactions` у этих карточек стал `[]` —
блок рисует штатную заглушку `t("card.blockEmpty")`.

Гейт держит инвариант в двух местах сразу (RU и EN): пустое отсутствие
данных выражается отсутствием записи, а не строкой-значением. Плюс
проверяется паритет длин `interactions` RU/EN — правка одной стороны без
другой его ломает.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_RU = ROOT / "docs" / "data.json"
DATA_EN = ROOT / "docs" / "data_en.json"

#: Значения `with`, которые означают «данных нет», а не название добавки.
#: Сравнение регистронезависимое, по strip().
PLACEHOLDERS = {"no data", "нет данных", "n/a", "n.a.", "-", "—", "–", "нет"}

#: Допустимые severity. Список закрытый: рендер строит класс `sev-<severity>`,
#: и незнакомое значение молча теряет оформление.
SEVERITIES = {"low", "medium", "high", "critical"}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ru_cards() -> list[dict]:
    data = _load(DATA_RU)
    assert isinstance(data, list), "docs/data.json должен быть списком карточек"
    return data


def _en_cards() -> dict[str, dict]:
    """docs/data_en.json — оверлей {_meta, supplements: {id: {...}}}."""
    data = _load(DATA_EN)
    assert isinstance(data, dict), "data_en.json должен быть объектом"
    supplements = data.get("supplements")
    assert isinstance(supplements, dict), "в data_en.json нет объекта supplements"
    return supplements


def _is_placeholder(entry: dict) -> bool:
    value = entry.get("with")
    return isinstance(value, str) and value.strip().lower() in PLACEHOLDERS


def _bad_entries(cards) -> list[str]:
    bad = []
    for card in cards:
        for entry in card.get("interactions") or []:
            if _is_placeholder(entry):
                bad.append(f"{card.get('id', '?')}: with = {entry.get('with')!r}")
    return bad


@pytest.fixture(scope="module")
def ru_cards() -> list[dict]:
    return _ru_cards()


@pytest.fixture(scope="module")
def en_cards() -> dict[str, dict]:
    return _en_cards()


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_no_placeholder_in_interactions(lang: str, ru_cards, en_cards) -> None:
    """`with` — имя добавки; «нет данных» выражается пустым списком."""
    cards = ru_cards if lang == "ru" else list(en_cards.values())
    bad = _bad_entries(cards)
    assert not bad, (
        f"в interactions[{lang}] снова лежит заглушка вместо названия добавки "
        f"(DATA-04, FIX-50): удалите запись целиком, пустой список рисует "
        f"штатную заглушку блока:\n  " + "\n  ".join(bad)
    )


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_interaction_with_is_non_empty_name(lang: str, ru_cards, en_cards) -> None:
    """Кроме заглушек: `with` не пустой и не пробельный — иначе пустая строка в UI."""
    cards = ru_cards if lang == "ru" else list(en_cards.values())
    bad = [
        f"{card.get('id', '?')}: with = {entry.get('with')!r}"
        for card in cards
        for entry in card.get("interactions") or []
        if not str(entry.get("with") or "").strip()
    ]
    assert not bad, f"пустое имя добавки в interactions[{lang}]:\n  " + "\n  ".join(bad)


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_interaction_severity_is_known(lang: str, ru_cards, en_cards) -> None:
    """severity попадает в CSS-класс `sev-<severity>` — только известные значения."""
    cards = ru_cards if lang == "ru" else list(en_cards.values())
    bad = [
        f"{card.get('id', '?')}: severity = {entry.get('severity')!r}"
        for card in cards
        for entry in card.get("interactions") or []
        if entry.get("severity") not in SEVERITIES
    ]
    assert not bad, (
        f"неизвестные severity в interactions[{lang}], допустимы {sorted(SEVERITIES)}:\n  "
        + "\n  ".join(bad)
    )


def test_interactions_count_is_stable(ru_cards, en_cards) -> None:
    """Счётчик записей после FIX-50: 199 - 51 = 148 в каждой локали.

    Число меняется только вместе с правкой данных — тогда обновите константу.
    Падение означает, что записи пропали или вернулись молча.
    """
    for lang, cards in (("ru", ru_cards), ("en", list(en_cards.values()))):
        total = sum(len(card.get("interactions") or []) for card in cards)
        assert total == 148, (
            f"interactions[{lang}]: записей {total}, ожидалось 148. "
            f"Если данные правились осознанно — обновите константу; если нет — "
            f"записи потеряны."
        )


def test_ru_en_interactions_lengths_match(ru_cards, en_cards) -> None:
    """Паритет длин RU/EN: EN — оверлей поверх RU, расхождение = дыра в переводе."""
    ru_len = {card["id"]: len(card.get("interactions") or []) for card in ru_cards}
    bad = [
        f"{cid}: ru {ru_len.get(cid, 'нет карточки')} != en {len(card.get('interactions') or [])}"
        for cid, card in en_cards.items()
        if len(card.get("interactions") or []) != ru_len.get(cid)
    ]
    assert not bad, (
        "длины interactions разъехались между data.json и data_en.json:\n  "
        + "\n  ".join(bad)
    )


def test_en_overlay_keys_exist_in_ru(ru_cards, en_cards) -> None:
    """Оверлей ключуется русским id: ключ без карточки — мёртвая запись."""
    ru_ids = {card["id"] for card in ru_cards}
    orphans = sorted(set(en_cards) - ru_ids)
    assert not orphans, f"в data_en.json ключи без карточки в data.json: {orphans[:10]}"


def test_content_dictionary_has_no_placeholder() -> None:
    """Источник данных тоже чист: scripts/build_interactions.py переносит
    content.INTERACTIONS в data.json, поэтому заглушка в словаре вернула бы
    дефект при следующей сборке."""
    from src import content

    bad = [
        f"{key}: with = {entry.get('with')!r}"
        for key, items in content.INTERACTIONS.items()
        for entry in items
        if _is_placeholder(entry)
    ]
    assert not bad, (
        "в src/content.py:INTERACTIONS снова заглушка в поле with — её "
        "перенесёт scripts/build_interactions.py:\n  " + "\n  ".join(bad)
    )
