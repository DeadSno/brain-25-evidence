"""Парсинг upper_limit в RU и EN (QA-06, FIX-39).

Из AUDIT-07: поле `upper_limit` встречалось только как имя поля в
`test_edu_top10.py` и как маппинг там же — английские единицы (`mg`, `g`,
`mcg`) не проверялись нигде, поэтому PROD-02 (дозировки в EN) не был
покрыт: `parseUpperLimit()` в `docs/hactar.js` знал только русские
единицы, и в EN проверка верхней нормы молча не срабатывала.

Тесты работают на настоящем коде: `tests/js_upper_limit_harness.js`
вырезает из `docs/hactar.js` блок «разбор дозировок» и исполняет его в
Node (jsdom не нужен — блок не трогает DOM). Тот же приём, что в
`test_js_behavior.py` + `tests/js_harness.js`.

Если node не установлен — skip, как в test_js_behavior.py: в CI node есть.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "js_upper_limit_harness.js"
HACTAR = ROOT / "docs" / "hactar.js"
NODE = shutil.which("node")

# Карточки, у которых upper_limit содержит число с единицей и в RU, и в EN.
# Единицы разные намеренно: мг, г, мкг, МЕ/IU.
CASES = [
    ("Магний", 350, "мг", "mg"),
    ("Цинк", 40, "мг", "mg"),
    ("Витамин C", 2000, "мг", "mg"),
    ("Витамин D", 4000, "МЕ", "IU"),
    ("Кофеин", 400, "мг", "mg"),
    ("Бакопа", 450, "мг", "mg"),
    ("Ашваганда", 1200, "мг", "mg"),
    ("Омега-3", 5, "г", "g"),
    ("Коллаген", 15, "г", "g"),
    ("B9", 1000, "мкг", "mcg"),
]

# Единицы из задания + те, что уже были в UNIT_SRC (КОЕ/CFU).
UNITS = ["мг", "mg", "г", "g", "мкг", "mcg", "µg", "ug",
         "МЕ", "IU", "мкмоль", "ммоль", "CFU", "КОЕ"]


@pytest.fixture(scope="module")
def js():
    if NODE is None:
        pytest.skip("node не установлен")
    if not HARNESS.exists():
        pytest.skip(f"нет {HARNESS}")
    if not HACTAR.exists():
        pytest.skip(f"нет {HACTAR}")
    r = subprocess.run([NODE, str(HARNESS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(ROOT), timeout=60)
    if not r.stdout.strip():
        pytest.fail(f"стенд не выдал JSON (rc={r.returncode}).\n"
                    f"stdout={r.stdout!r}\nstderr={r.stderr!r}")
    data = json.loads(r.stdout)
    if not data.get("ok"):
        pytest.fail(f"стенд упал: {data.get('error')}")
    return data


def test_harness_extracts_production_block(js):
    """Стенд режет hactar.js по маркерам: если разметка файла изменится,
    тест должен упасть здесь, а не тихо проверять пустоту."""
    assert "мкг" in js["unit_src"]
    assert "mg" in js["unit_src"]
    assert "no" in js["no_ul_src"].lower()
    assert len(js["cases"]) == 130


# ─────────────────────────── 1. RU ───────────────────────────

@pytest.mark.parametrize("card,value,unit_ru,unit_en", CASES)
def test_ru_upper_limit_parsed(js, card, value, unit_ru, unit_en):
    """Русская строка даёт то же число, что написано в data.json."""
    got = js["cases"][card]["ru"]
    assert got is not None, f"{card}: RU upper_limit не распознан"
    assert got["mg"] == pytest.approx(value)
    assert got["unit"] == unit_ru


# ─────────────────────────── 2. EN ───────────────────────────

@pytest.mark.parametrize("card,value,unit_ru,unit_en", CASES)
def test_en_upper_limit_parsed(js, card, value, unit_ru, unit_en):
    """EN-строка (data_en.json) парсится теми же правилами.

    До FIX-39 здесь был null для всего, кроме IU: UNIT_SRC знал только
    «мг/г/мкг», а оверлей пишет «mg/g/mcg».
    """
    case = js["cases"][card]
    assert case["en_text"], f"{card}: пустой EN upper_limit"
    got = case["en"]
    assert got is not None, f"{card}: EN upper_limit не распознан: {case['en_text']!r}"
    assert got["mg"] == pytest.approx(value)
    assert got["unit"] == unit_en


# ─────────────────────── 3. паритет RU/EN ───────────────────────

def test_ru_en_parity_over_all_cards(js):
    """Для всех 130 карточек: либо обе строки дают null, либо обе — одно
    и то же число. Асимметрия означала бы, что в EN проверка нормы не
    работает или работает иначе, чем в RU."""
    diff = []
    for cid, case in js["cases"].items():
        ru, en = case["ru"], case["en"]
        if (ru is None) != (en is None):
            diff.append((cid, ru, en, case["ru_text"], case["en_text"]))
        elif ru is not None and abs(ru["mg"] - en["mg"]) > 1e-9:
            diff.append((cid, ru, en, case["ru_text"], case["en_text"]))
    assert not diff, "расхождение RU/EN:\n" + "\n".join(
        f"{c}: ru={ru} en={en}\n  ru_text={rt!r}\n  en_text={et!r}"
        for c, ru, en, rt, et in diff)


def test_parity_covers_units_by_scale(js):
    """Число совпадает, а единица в EN латинская: мг↔mg, г↔g, мкг↔mcg,
    МЕ↔IU. Это и есть проверка, что оверлей переводит единицы, а не
    только текст."""
    pairs = {"мг": "mg", "г": "g", "мкг": "mcg", "МЕ": "IU"}
    bad = [(cid, case["ru"], case["en"]) for cid, case in js["cases"].items()
           if case["ru"] and pairs.get(case["ru"]["unit"]) != case["en"]["unit"]]
    assert not bad, f"единицы RU/EN не парные: {bad}"


# ─────────────────────── 4. NO_UL ───────────────────────

@pytest.mark.parametrize("name", ["en_no_ul", "ru_no_ul", "en_not_specified", "empty"])
def test_no_ul_markers_give_null(js, name):
    """«Нормы нет» — это null, а не первое число из фразы.

    Регрессия, которую ловим: «There is no formal UL; 3-5 g/day is safe»
    до FIX-39 парсилось как UL = 5 g (в EN маркеров «нет нормы» не было).
    """
    probe = next(p for p in js["probes"] if p["name"] == name)
    assert probe["result"] is None, f"{name}: {probe['text']!r} -> {probe['result']}"


def test_no_ul_cards_are_null_in_both_locales(js):
    """Карточки без формального UL (креатин, мелатонин, сульфорафан)
    должны быть null в обеих локалях — иначе в EN появится ложная норма."""
    for card in ("Креатин", "Мелатонин", "Сульфорафан"):
        case = js["cases"][card]
        assert case["ru"] is None, f"{card}: RU должен быть null, а {case['ru']}"
        assert case["en"] is None, f"{card}: EN должен быть null, а {case['en']}"


# ─────────────────────── 5. UNIT_SRC ───────────────────────

@pytest.mark.parametrize("unit", UNITS)
def test_unit_src_recognises_unit(js, unit):
    """Каждая единица из задания распознаётся: «100 <unit>/day» -> 100.

    Пробел перед единицей в UNIT_SRC не входит — число и единица
    разделяются `\\s*` в самом шаблоне.
    """
    got = js["units"][unit]
    assert got is not None, f"UNIT_SRC не знает единицу {unit!r}"
    assert got["mg"] == 100


def test_unit_src_latin_units_regression(js):
    """QA-06b: именно этих трёх альтернатив не было — из-за них EN не
    парсился. Проверяем по источнику регулярки, а не по поведению: так
    тест переживёт смену проб."""
    src = js["unit_src"]
    for unit in ("mg", "mcg", "g"):
        assert unit in src, f"в UNIT_SRC нет {unit!r}: {src}"


# ─────────────────────── 6. границы ───────────────────────

def test_boundaries_mg_and_iu(js):
    probes = {p["name"]: p["result"] for p in js["probes"]}
    assert probes["en_350_mg"]["mg"] == 350
    assert probes["en_4000_iu"]["mg"] == 4000
    assert probes["ru_2000_mg"]["mg"] == 2000


def test_boundaries_fraction_and_comma(js):
    """0.5 g остаётся 0.5 g: parseUpperLimit не конвертирует, конверсия —
    в toMg (проверяется ниже). Запятая как десятичный разделитель — RU."""
    probes = {p["name"]: p["result"] for p in js["probes"]}
    assert probes["en_0_5_g"] == {"mg": 0.5, "unit": "g"}
    assert probes["ru_comma_g"] == {"mg": 0.5, "unit": "г"}


def test_boundaries_prefers_daily_over_single(js):
    """«single 200 mg, up to 400 mg/day» — норма суточная, берём 400."""
    probes = {p["name"]: p["result"] for p in js["probes"]}
    assert probes["en_single_vs_daily"]["mg"] == 400
    assert probes["en_range"]["mg"] == 450


def test_to_mg_converts_latin_units(js):
    """toMg — то, чем doseInfo сравнивает введённую дозу с нормой.
    Без латинских единиц EN-сравнение падало в ветку sameUnit."""
    assert js["toMg"]["0.5_g"] == 500
    assert js["toMg"]["500_mg"] == 500
    assert js["toMg"]["1000_mcg"] == 1
    assert js["toMg"]["350_IU"] is None  # МЕ к мг не приводится


def test_same_unit_bridges_ru_and_latin(js):
    assert js["sameUnit"]["mg_vs_мг"] is True
    assert js["sameUnit"]["IU_vs_МЕ"] is True
    assert js["sameUnit"]["mcg_vs_мкг"] is True
    assert js["sameUnit"]["g_vs_мг"] is False
