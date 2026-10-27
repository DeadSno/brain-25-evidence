"""Тест беременностного предупреждения (QA-05, PROD-01).

Ловит регресс: предупреждение о противопоказании при беременности должно
работать и в RU, и в EN. Раньше `pregRisk()` в `docs/hactar.js:2864`
сверяло `rec.caution` с русской регуляркой `PREG_RE`, и в EN совпадений не
было — баннер оставался `hidden`.

Фикс FIX-01: добавлен структурный флаг `pregnancy_contraindicated: true`
у 6 карточек (Шатавари, Лаванда, Глутатион, PQQ, MSM, Гимнема) в обоих
файлах данных, и в `pregRisk()` флаг проверяется **до** `PREG_RE`.

Маркеры: не требуют браузера, не требуют сети.

Структура файлов:
  * docs/data.json — list[dict], у каждой карточки поле `id`.
  * docs/data_en.json — dict с ключами `_meta` и `supplements`;
    `supplements` — dict, ключ = русский id карточки, значение = карточка.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
DATA_EN_JSON = ROOT / "docs" / "data_en.json"
HACTAR_JS = ROOT / "docs" / "hactar.js"

# 6 карточек с противопоказанием при беременности (из PROD-01)
PREGNANCY_CARDS = [
    "Шатавари",
    "Лаванда",
    "Глутатион",
    "PQQ",
    "MSM",
    "Гимнема",
]

# Контрольная карточка без флага
CONTROL_CARD = "Магний"


def _load_json(path: Path):
    assert path.exists(), f"нет файла: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _ru_cards(data: list[dict]) -> dict[str, dict]:
    """data.json — list[dict], ключ по полю `id`."""
    return {c["id"]: c for c in data}


def _en_cards(data: dict) -> dict[str, dict]:
    """data_en.json — dict {_meta, supplements}, ключ = русский id."""
    supplements = data.get("supplements", {})
    assert isinstance(supplements, dict), (
        f"data_en.json: ожидался dict в 'supplements', получен {type(supplements)}"
    )
    return supplements


def _flagged_ids_ru(data: list[dict]) -> set[str]:
    return {c["id"] for c in data if c.get("pregnancy_contraindicated") is True}


def _flagged_ids_en(data: dict) -> set[str]:
    return {cid for cid, card in data.get("supplements", {}).items()
            if card.get("pregnancy_contraindicated") is True}


# ───────────────────────────── Тест 1: RU ─────────────────────────────

@pytest.mark.parametrize("card_id", PREGNANCY_CARDS)
def test_ru_card_has_pregnancy_flag(card_id: str) -> None:
    """Каждая карточка из списка PROD-01 имеет флаг в data.json (RU)."""
    data = _load_json(DATA_JSON)
    by_id = _ru_cards(data)
    assert card_id in by_id, f"{card_id}: нет карточки в data.json"
    assert by_id[card_id].get("pregnancy_contraindicated") is True, (
        f"{card_id}: pregnancy_contraindicated !== true в data.json"
    )


# ───────────────────────────── Тест 2: EN ─────────────────────────────

@pytest.mark.parametrize("card_id", PREGNANCY_CARDS)
def test_en_card_has_pregnancy_flag(card_id: str) -> None:
    """Каждая карточка из списка PROD-01 имеет флаг в data_en.json (EN)."""
    data = _load_json(DATA_EN_JSON)
    by_id = _en_cards(data)
    assert card_id in by_id, f"{card_id}: нет карточки в data_en.json (supplements)"
    assert by_id[card_id].get("pregnancy_contraindicated") is True, (
        f"{card_id}: pregnancy_contraindicated !== true в data_en.json"
    )


# ───────────────────────────── Тест 3: паритет флагов ─────────────────

def test_pregnancy_flag_parity() -> None:
    """Множества id с флагом совпадают в data.json и data_en.json (6 = 6)."""
    ru_data = _load_json(DATA_JSON)
    en_data = _load_json(DATA_EN_JSON)
    ru_flagged = _flagged_ids_ru(ru_data)
    en_flagged = _flagged_ids_en(en_data)
    assert ru_flagged == en_flagged, (
        f"рассинхрон флагов: ru_only={ru_flagged - en_flagged}, "
        f"en_only={en_flagged - ru_flagged}"
    )
    assert len(ru_flagged) == 6, (
        f"ожидалось 6 карточек с флагом в RU, получено {len(ru_flagged)}: {sorted(ru_flagged)}"
    )
    assert len(en_flagged) == 6, (
        f"ожидалось 6 карточек с флагом в EN, получено {len(en_flagged)}: {sorted(en_flagged)}"
    )


# ───────────────────────────── Тест 4: логика pregRisk (Python эмуляция) ─

def test_pregnant_logic_ru() -> None:
    """Эмуляция pregRisk для RU: 6 карточек → true, Магний → false."""
    data = _load_json(DATA_JSON)
    by_id = _ru_cards(data)
    for card_id in PREGNANCY_CARDS:
        rec = by_id[card_id]
        # pregRisk: флаг === true → true (до PREG_RE)
        assert rec.get("pregnancy_contraindicated") is True, f"{card_id}: флаг не true"
    # Контроль: Магний не должен иметь флага
    assert by_id.get(CONTROL_CARD, {}).get("pregnancy_contraindicated") is not True, (
        f"{CONTROL_CARD}: неожиданный флаг pregnancy_contraindicated"
    )


def test_pregnant_logic_en() -> None:
    """Эмуляция pregRisk для EN: 6 карточек → true, Магний → false."""
    data = _load_json(DATA_EN_JSON)
    by_id = _en_cards(data)
    for card_id in PREGNANCY_CARDS:
        rec = by_id[card_id]
        assert rec.get("pregnancy_contraindicated") is True, f"{card_id}: флаг не true"
    assert by_id.get(CONTROL_CARD, {}).get("pregnancy_contraindicated") is not True, (
        f"{CONTROL_CARD}: неожиданный флаг pregnancy_contraindicated"
    )


# ───────────────────────────── Тест 5: регресс hactar.js ───────────────

def test_hactar_js_flag_before_preg_re() -> None:
    """В hactar.js `rec.pregnancy_contraindicated === true` стоит ДО `PREG_RE.test`."""
    js = HACTAR_JS.read_text(encoding="utf-8")
    flag_line = "rec.pregnancy_contraindicated === true"
    assert flag_line in js, "hactar.js: нет проверки pregnancy_contraindicated"

    flag_pos = js.index(flag_line)
    preg_re_pos = js.index("PREG_RE.test")
    assert flag_pos < preg_re_pos, (
        "hactar.js: pregnancy_contraindicated проверяется ПОСЛЕ PREG_RE.test — "
        "порядок нарушен, регресс возможен"
    )


def test_hactar_js_preg_re_kept_as_fallback() -> None:
    """PREG_RE оставлен в hactar.js как fallback (не удалён)."""
    js = HACTAR_JS.read_text(encoding="utf-8")
    assert "PREG_RE" in js, "hactar.js: PREG_RE удалён — fallback потерян"
