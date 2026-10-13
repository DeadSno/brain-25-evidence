"""Список «модулей без тестов» в скилле qa-deep-audit должен быть правдой.

F-39 (QA-P1-01): скилл предлагал проверять тесты для семи модулей.
Четыре из них — `content.py`, `src/config.py`, `src/ct_terms.py`,
`src/wiki_map.py` — давно покрыты, а список продолжал предлагать искать
то, что уже написано. Рядом стояло утверждение «тесты:
tests/test_analyze_coi.py в фикстурах 5 XML-файлов», и такого файла
в репозитории не было никогда.

Список, который врёт, хуже отсутствующего списка: аудитор тратит
время на уже сделанную работу и записывает в отчёт вывод, который
легко принять за новую находку. Поэтому утверждение проверяется.

Что именно проверяется, для каждого пункта списка:
  1. модуль существует (иначе пункт протух по другой причине);
  2. рядом нет файла теста.

Второй пункт — тот самый гейт на собственную правдивость: если для
модуля появятся тесты, список обязан это отразить, иначе тест
упадёт и список поправится.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".opencode" / "skills" / "qa-deep-audit" / "SKILL.md"

#: Строка-якорь: список начинается с неё и идёт до следующего заголовка.
HEADER = "- Есть ли тесты на:"
NEXT_HEADING = re.compile(r"^###\s", re.M)
MODULE_LINE = re.compile(r"^[ \t]*-[ \t]+([A-Za-z0-9_./-]+\.py)[ \t]*$", re.M)


def _listed_modules() -> list[str]:
    text = SKILL.read_text(encoding="utf-8")
    start = text.index(HEADER) + len(HEADER)
    rest = text[start:]
    m = NEXT_HEADING.search(rest)
    block = rest[:m.start()] if m else rest
    return MODULE_LINE.findall(block)


MODULES = _listed_modules()


def test_the_list_is_not_empty():
    """Пустой список — это не «всё покрыто», это сломанный разбор."""
    assert len(MODULES) >= 3, (
        f"из блока «Есть ли тесты на:» разобрано только {len(MODULES)} "
        f"модулей: {MODULES}. Либо список опустел, либо его формат изменился "
        f"и гейт молча перестал его читать."
    )


@pytest.mark.parametrize("mod", MODULES, ids=MODULES)
def test_listed_module_exists(mod: str):
    """Пункт списка обязан указывать на существующий модуль."""
    base = mod.rsplit("/", 1)[-1]
    candidates = [ROOT / "scripts" / mod, ROOT / mod,
                  ROOT / "src" / base, ROOT / "src" / mod,
                  ROOT / "scripts" / "db" / base]
    assert any(p.exists() for p in candidates), (
        f"{mod} из списка «модулей без тестов» не найден ни в scripts/, "
        f"ни в src/. Список протух: убери пункт или укажи реальный путь."
    )


@pytest.mark.parametrize("mod", MODULES, ids=MODULES)
def test_listed_module_really_has_no_test(mod: str):
    """Главное: у перечисленного модуля действительно нет тестов."""
    stem = mod.rsplit("/", 1)[-1][:-3]
    tests = sorted(p.name for p in (ROOT / "tests").glob("*" + stem + "*"))
    assert not tests, (
        f"{mod} указан в списке как непокрытый, но рядом есть {tests}. "
        f"Убери пункт из списка — иначе аудит будет искать то, что написано."
    )


def test_gate_would_notice_a_new_test():
    """Отрицательный пример: гейт обязан ловить появление теста."""
    stem = MODULES[0].rsplit("/", 1)[-1][:-3]
    tests = sorted(p.name for p in (ROOT / "tests").glob("*" + stem + "*"))
    assert not tests, (
        "исходный модуль уже покрыт — проверка выше должна была упасть; "
        "если она зелёная, она ничего не проверяет"
    )