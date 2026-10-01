"""Тесты классификатора блокировки DuckDB (QA_AUDIT P0-3).

Классификатор живёт в conftest.is_lock_error. Без собственных тестов он может
тихо перестать срабатывать — например, если сообщение об ошибке на другой
локали или в другой версии DuckDB перестанет содержатьKnown-маркеры. Тогда
16 тестов снова упадут с ERROR, и это будет выглядеть как регрессия данных,
хотя дело в окружении. Именно такой отказ уже случался.
"""
import re

import pytest

# Импорт по полному пути, а не `from conftest import ...`: в корне репозитория
# лежит свой conftest.py (3 строки, только sys.path), и он перехватывает
# короткое имя `conftest`. tests/ — пакет (есть __init__.py), поэтому
# tests.conftest адресуется однозначно.
from tests.conftest import LOCK_MARKERS, is_lock_error

# Дословные сообщения, снятые с реальных прогонов.
REAL_WINDOWS_RU = (
    'IO Error: Cannot open file "C:\\analytics\\brain-25-evidence\\data\\db\\brain.duckdb": '
    'Процесс не может получить доступ к файлу, так как этот файл занят другим процессом.\n\n'
    "File is already open in \nC:\\Program Files\\nodejs\\node.exe (PID 38456)"
)
REAL_WINDOWS_EN = (
    'IO Error: Cannot open file "/repo/data/db/brain.duckdb": The process cannot access '
    "the file because it is being used by another process."
)
DUCKDB_EN = (
    'IO Error: Could not set lock on file "/repo/data/db/brain.duckdb": Conflicting lock '
    "is held in PID 12345."
)
LINUX_BUSY = (
    'IO Error: Cannot open file "/repo/data/db/brain.duckdb": Device or resource busy'
)


@pytest.mark.parametrize("msg", [REAL_WINDOWS_RU, REAL_WINDOWS_EN, DUCKDB_EN, LINUX_BUSY])
def test_lock_messages_recognised(msg):
    assert is_lock_error(Exception(msg)) is True


@pytest.mark.parametrize("msg", [
    # Файл не создан — это не лок, а отсутствие данных: должен упасть, не скипнуться.
    'IO Error: Cannot open file "/repo/data/db/brain.duckdb": No such file or directory',
    # Файл повреждён — тоже не лок.
    "IO Error: The file /repo/brain.duckdb is corrupted and cannot be read",
    # Нет прав.
    "IO Error: Permission denied",
    # Ничего общего с блокировкой.
    "Catalog Error: Table with name supplement does not exist!",
])
def test_non_lock_messages_not_recognised(msg):
    assert is_lock_error(Exception(msg)) is False


def test_every_marker_is_lowercase():
    """Регрессия-ловушка: is_lock_error() сравнивает с .lower(), поэтому маркер
    в верхнем регистре никогда не сработает и проверка станет тихо бесполезной."""
    for m in LOCK_MARKERS:
        assert m == m.lower(), f"маркер {m!r} содержит заглавные — не сработает"


def test_real_ru_message_has_no_lock_or_held():
    """Документирует, ПОЧЕМУ маркеров так много.

    Исходное предложение фикса было `if "lock" in ... or "held" in ...` — на
    Windows (RU и EN) оно не срабатывает: этих подстрок в сообщении просто нет.
    """
    low = REAL_WINDOWS_RU.lower()
    assert "lock" not in low
    assert "held" not in low
    assert is_lock_error(Exception(REAL_WINDOWS_RU)) is True
