"""version.json показывает настоящее число тестов.

Та же болезнь, что была с `methodology.html`, только в другом месте. На
`index.html` есть пустой `<span data-version="tests">`, который `version.js`
заполняет из `docs/version.json`. Долгое время там стояло `"tests": 143`,
тогда как прогон давал 727 — и никто этого не замечал, потому что число
подставлялось в рантайме и не встречалось ни в одной строке разметки:
поиск по исходникам его не находил.

Тест закрывает дыру: он считает реально собранные тесты и требует, чтобы
version.json совпадал.

Цена решения осознанная: после добавления любого теста файл придётся
обновить. Это ровно то трение, которое нужно — иначе число снова
разъедется с правдой молча.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_JSON = ROOT / "docs" / "version.json"


def _collected_count() -> int:
    """Сколько тестов реально собирает pytest в этом окружении."""
    out = subprocess.run(
        ["python", "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    tail = (out.stdout or "").strip().splitlines()[-1]
    m = re.search(r"(\d+)\s+tests?\s+collected", tail)
    if not m:
        m = re.search(r"(\d+)\s+tests?\s+collected", out.stdout or "")
    assert m, f"не удалось разобрать вывод pytest --collect-only:\n{tail}"
    return int(m.group(1))


def test_version_json_is_valid():
    v = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    for key in ("app", "data", "tests"):
        assert key in v, f"в version.json нет поля {key}"
    assert isinstance(v["tests"], int) and v["tests"] > 0


def test_version_json_tests_match_collected():
    """Число, которое видит посетитель, == число реально собранных тестов."""
    v = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    actual = _collected_count()
    assert v["tests"] == actual, (
        f"version.json обещает {v['tests']} тестов, "
        f"pytest собирает {actual}. Обнови docs/version.json."
    )


def test_test_counter_is_rendered_somewhere():
    """Счётчик не должен болтаться в разметке мёртвым грузом.

    Смысл проверки — фиксировать контракт: раз есть поле `tests` в
    version.json, значит где-то должен быть спан, который его показывает.
    Иначе правка version.json ничего не изменит для пользователя.
    """
    v = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    if "tests" not in v:
        pytest.skip("в version.json нет поля tests")
    pages = list((ROOT / "docs").glob("*.html"))
    with_span = [p.name for p in pages if 'data-version="tests"' in p.read_text(encoding="utf-8")]
    assert with_span, "в docs/*.html нет ни одного data-version=\"tests\""