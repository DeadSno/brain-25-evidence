"""Общие фикстуры для тестов brain-25-evidence."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "data" / "db" / "brain.duckdb"


def pytest_collection_modifyitems(config, items):
    """Выключить браузерные e2e и визуальные снапшоты по умолчанию.

    Оба гейта — на переменной окружения, а НЕ на `-m` в addopts: `-m`,
    переданный в командной строке, ПЕРЕКРЫВАЕТ addopts. Это не теория,
    измерено на этой копии:

        pytest --collect-only -q                    -> 754/791 (37 deselected)
        pytest --collect-only -q -m "not e2e"       -> 789/791 (2 deselected)

    То есть с `-m "not snapshots"` в addopts любая другая `-m` в командной
    строке (а такая команда есть в инструкциях проекта) возвращала 37
    тяжёлых тестов и превращала быстрый прогон в 100-секундный.

    Снапшоты — самые тяжёлые тесты в проекте: 37 попиксельных сравнений PNG
    против эталонов, полный прогон ~100 с против ~4 с без них. Для быстрых
    коммитов они не нужны, для миграции дизайн-системы — обязательны.

    Включить: RUN_SNAPSHOTS=1 pytest -q -m snapshots

    Тесты доступности (tests/test_a11y_axe.py) несут только маркер `a11y` и
    снимаются отдельным фильтром: им тоже нужен браузер и сервер, но команда
    запуска у них своя — RUN_A11Y=1 pytest -q -m a11y.
    """
    if os.environ.get("RUN_E2E") == "1":
        pass  # e2e-гейт ниже
    else:
        skip = pytest.mark.skip(
            reason="e2e выключены по умолчанию (долгий прогон, нужен браузер). "
                   "Запуск: RUN_E2E=1 pytest -q -m e2e"
        )
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip)

    # Снапшоты и тесты доступности снимаются НЕЗАВИСИМЫМИ фильтрами: у них
    # разные маркеры и разные команды. Раньше a11y-тесты несли оба маркера, и
    # фильтр по `snapshots` отбрасывал их — замерено: `RUN_A11Y=1 pytest -m a11y`
    # давал «754 deselected, 0 selected», то есть гейт был зелёным вхолостую.
    # Теперь пересечения нет, и каждый гейт включается своей переменной:
    #   RUN_SNAPSHOTS=1 -> только снапшоты
    #   RUN_A11Y=1      -> только доступность
    #   ничего          -> быстрый прогон без браузера
    if not os.environ.get("RUN_SNAPSHOTS"):
        items[:] = [item for item in items if "snapshots" not in item.keywords]

    if not os.environ.get("RUN_A11Y"):
        items[:] = [item for item in items if "a11y" not in item.keywords]

    # 	abs (tests/test_tabs_interaction.py, v5.4.1): клик по вкладкам.
    # Требует живого сервера на :8000 и браузеров Playwright, поэтому
    # снят здесь, а не через -m в addopts: командная строка -m "..."
    # перекрывает addopts и включила бы 42 теста неожиданно — ровно то,
    # из-за чего e2e вынесен в отдельную настройку.
    # Запуск: \="1"; pytest -q -m tabs
    if not os.environ.get("RUN_TABS"):
        items[:] = [item for item in items if "tabs" not in item.keywords]


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def data_json_path(project_root: Path) -> Path:
    return project_root / "docs" / "data.json"


# ──────────────────────── DuckDB: лок от внешнего процесса ────────────────────────
#
# QA_AUDIT P0-3. brain.duckdb открывается в read_only, но DuckDB всё равно берёт
# на файл блокировку, и если файл держит посторонний процесс (в нашем случае —
# MCP-сервер `duckdb-mcp-stdio.mjs`), connect() бросает IOException. Прежние
# фикстуры в test_sql.py и test_integration_api_db.py проверяли только
# DB_PATH.exists(), поэтому 16 тестов падали с ERROR, и результат прогона зависел
# от того, запущен ли у разработчика фоновый MCP-процесс.
#
# Теперь это SKIP: «замаскировать» ошибку нельзя, но «замаскировать» её как
# зелёный прогон тоже неправильно — skip честнее, потому что видно, что тесты
# не выполнялись.

#: Маркеры сообщения о блокировке. Проверено на трёх платформах/локалях:
#:   Windows RU: "Процесс не может получить доступ к файлу, так как этот файл
#:               занят другим процессом.\n\nFile is already open in <path> (PID n)"
#:   Windows EN: "...because it is being used by another process"
#:   Linux CI:   "Device or resource busy" / "Resource temporarily unavailable"
#:   DuckDB:     "Could not set lock on file" / "Conflicting lock is held"
#: ВАЖНО: подстроки "lock"/"held" НЕ срабатывают на сообщениях Windows — там их
#: просто нет, поэтому список шире и включает русские варианты.
LOCK_MARKERS = (
    "lock",
    "already open in",
    "being used by another process",
    "used by another process",
    "device or resource busy",
    "resource temporarily unavailable",
    "занят другим процессом",
    "не может получить доступ",
)


def is_lock_error(exc: BaseException) -> bool:
    """Похоже ли исключение на блокировку файла посторонним процессом?

    Ложноотрицательный результат означает 16 ERROR вместо SKIP, поэтому список
    маркеров намеренно широкий. Ложноположительный (например, «битый файл»,
    где в тексте случайно есть «lock») вернёт skip вместо падения — поэтому
    всё, что НЕ распознано как лок, пробрасывается наружу и падает как раньше.
    """
    return any(m in str(exc).lower() for m in LOCK_MARKERS)


@pytest.fixture(scope="module")
def db_conn():
    """Read-only соединение с brain.duckdb.

    Skip, если файл держит другой процесс. Любая другая ошибка подключения
    (битый файл, нет прав, несовместимая версия) пробрасывается как есть.
    """
    if not DB_PATH.exists():
        pytest.skip(f"DuckDB не создан: {DB_PATH} (python scripts/db/import_to_duckdb.py)")
    duckdb = pytest.importorskip("duckdb")
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
    except Exception as exc:  # noqa: BLE001 — классифицируем и решаем ниже
        if is_lock_error(exc):
            # Текст исключения многострочный («File is already open in\n<PATH>»),
            # а reason в skip попадает в прогресс-строку pytest — схлопываем в
            # одну строку, иначе ломается вывод и итоговая сводка.
            detail = " ".join(str(exc).split())
            pytest.skip(f"brain.duckdb занят другим процессом (MCP duckdb?) — тесты БД пропущены: {detail}")
        raise
    try:
        yield conn
    finally:
        conn.close()
