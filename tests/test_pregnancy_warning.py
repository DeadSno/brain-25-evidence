"""Тест предупреждения о беременности: PARITY RU vs EN (LEGAL-03, FIX-48).

PREG_RE в docs/hactar.js должен триггерить и на русских, и на английских
карточках с терминами беременности/лактации. Ранее regex был только
руссифицирован (беременн), поэтому в EN предупреждение молча пропадало
(баннер hidden, текст пустой).

Стенд tests/js_preg_harness.js вырезает определение `var PREG_RE = ...` из
production hactar.js (по маркеру, не по номерам строк) и исполняет в Node vm,
отдавая JSON с результатами test() для каждой пары RU/EN карточек.
"""

import json
import subprocess
import sys

import pytest

HACTAR_JS = "docs/hactar.js"
DATA_RU = "docs/data.json"
DATA_EN = "docs/data_en.json"


def run_harness():
    """Запускает Node-стенд и возвращает распарсенный JSON."""
    proc = subprocess.run(
        ["node", "tests/js_preg_harness.js"],
        capture_output=True, timeout=30,
    )
    if proc.returncode != 0:
        pytest.fail(f"js_preg_harness.js упал с кодом {proc.returncode}: {proc.stderr.decode('utf-8', errors='replace')}")
    try:
        return json.loads(proc.stdout.decode('utf-8'))
    except json.JSONDecodeError as e:
        pytest.fail(f"js_preg_harness.js выдал не JSON: {proc.stdout[:200]} — {e}")


def test_preg_re_is_reg_exp():
    """PREG_RE извлекается и является рабочей регуляркой."""
    data = run_harness()
    assert data["ok"], f"Харнес не удался: {data.get('error')}"
    assert data["summary"]["ru_total"] == 130
    assert data["summary"]["en_total"] == 130


def test_preg_re_ru_matches():
    """Тест 1 (RU): карточки с «беременн» в caution → PREG_RE.test() = True."""
    data = run_harness()
    ru_matches = data["summary"]["ru_matches"]
    # Известно 6 карточек (Шатавари, Лаванда, Глутатион, PQQ, MSM, Гимнема)
    assert ru_matches >= 3, f"Ожидалось ≥3 RU-совпадений, получено {ru_matches}"
    assert ru_matches <= 8, f"Слишком много RU-совпадений: {ru_matches}"


def test_preg_re_en_matches():
    """Тест 2 (EN): карточки с pregnant/breastfeeding/lactation → PREG_RE.test() = True."""
    data = run_harness()
    en_matches = data["summary"]["en_matches"]
    # До FIX-48 было 0, теперь должно быть столько же, сколько в RU (±2)
    assert en_matches >= 3, f"Ожидалось ≥3 EN-совпадений, получено {en_matches}"


def test_preg_re_parity():
    """Тест 3 (паритет): число RU- и EN-совпадений отличается не более чем на 2."""
    data = run_harness()
    ru = data["summary"]["ru_matches"]
    en = data["summary"]["en_matches"]
    diff = abs(ru - en)
    assert diff <= 2, f"Непартет RU/EN: RU={ru}, EN={en}, разница={diff}"


def test_preg_re_negative():
    """Тест 4 (отрицательный): карточка без pregnancy-слов → PREG_RE.test() = False."""
    data = run_harness()
    cases = data["cases"]
    # Ищем карточку, которая точно не должна триггерить (Магний, Цинк — без беременности)
    for _id, case in cases.items():
        ru_caution = case["ru_caution"].lower()
        en_caution = case["en_caution"].lower()
        has_preg_ru = any(t in ru_caution for t in ["беременн", "лактац", "кормлен", "грудн"])
        has_preg_en = any(t in en_caution for t in ["pregnan", "breastfeed", "lactat", "nursing", "trimester", "expectant"])
        if not has_preg_ru and not has_preg_en:
            assert not case["ru_match"], f"RU ложное срабатывание на {_id}"
            assert not case["en_match"], f"EN ложное срабатывание на {_id}"
            return
    pytest.fail("Не найдена подходящая отрицательная карточка без терминов беременности")
