"""Общие фикстуры для тестов brain-25-evidence."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "data" / "db" / "brain.duckdb"


# ─────────────── Гейты по переменным окружения: УДАЛЕНЫ (v5.6.5) ───────────────
#
# До v5.6.5 здесь был pytest_collection_modifyitems, который вешал skip по
# переменным окружения: RUN_SNAPSHOTS / RUN_A11Y / RUN_TABS / RUN_GRAPH /
# RUN_MOBILE / RUN_E2E. `pytest -q` показывал 235-262 skipped и выглядел
# успешным, хотя браузерные тесты (snapshots, a11y, tabs, graph, mobile375,
# e2e) не выполнялись вовсе — та же ловушка «N skipped выглядит как успех»,
# которую scripts/check_snapshot_run.py уже ловит для другой причины.
#
# Теперь гейтов НЕТ: `pytest -q` запускает всё. Сервер :8000 поднимает
# autouse-фикстура live_server (для всех браузерных тестов), общий
# sync_playwright() на сессию даёт playwright_instance.
#
# Подмножества задаются обычным `-m` (маркеры описаны в pytest.ini):
#   pytest -q -m snapshots
#   pytest -q -m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"
#
# Маркеры `network` нет и не было нужды: ни один тест в tests/ не ходит в сеть.


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


# ──────────────────────────── live_server ─────────────────────────────
#
# Session-фикстура, поднимающая локальный http.server на :8000 с корнем
# docs/. Безусловная (autouse): визуальные/браузерные тесты (снапшоты, a11y,
# tabs, graph, mobile375) ходят на http://localhost:8000 и сравнивают
# страницы ИМЕННО этого репозитория.
#
# До v5.6.5 сервер поднимался только при RUN_SNAPSHOTS=1, поэтому остальные
# браузерные гейты оставались скипнутыми по причине «нет сервера», хотя
# сервер им нужен ровно тот же.
#
# Порт 8000 фиксирован: все браузерные тесты ожидают SNAPSHOT_BASE_URL
# http://localhost:8000 (константа BASE_URL в test_*.py).


def _serves_this_repo(port: int = 8000, timeout: float = 2.0) -> bool:
    """На :8000 уже отдаётся docs/ ИМЕННО этого репозитория?

    Сверяется sha256 style.css — тот же признак, что в _check_server() у
    браузерных тестов. Без сверки чужой сервер на :8000 заставил бы
    live_server молча пропустить старт, а тесты проверяли бы не тот код.
    """
    import hashlib
    import urllib.request

    local = ROOT / "docs" / "style.css"
    if not local.exists():
        return False
    try:
        with urllib.request.urlopen(
            f"http://localhost:{port}/style.css", timeout=timeout
        ) as resp:
            served = resp.read()
    except Exception:  # noqa: BLE001 — любой сбой = «не наш сервер»
        return False
    return hashlib.sha256(served).hexdigest() == hashlib.sha256(
        local.read_bytes()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """Поднять http.server :8000 на docs/ для всех браузерных тестов.

    Безусловная: снапшоты, a11y, tabs, graph и mobile375 ходят на
    http://localhost:8000, и раньше сервер поднимался только при
    RUN_SNAPSHOTS=1 — остальные гейты оставались красными/скипнутыми по
    причине «нет сервера», хотя сервер им нужен ровно тот же.

    Если :8000 уже отдаёт docs/ этого репозитория — используется он
    (повторный http.server упал бы на занятом порту).
    """
    if _serves_this_repo():
        yield None
        return
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8000"],
        cwd=str(ROOT / "docs"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def playwright_instance():
    """Один sync_playwright() на всю сессию — для ВСЕХ браузерных тестов.

    Раньше каждый модуль (snapshots, a11y, tabs, graph, mobile375) открывал
    свой session-scoped `sync_playwright()`. Два таких контекста не живут
    одновременно: второй __enter__ видит работающий event loop первого и
    бросает `Error: It looks like you are using Playwright Sync API inside
    the asyncio loop`. Из-за этого при прогоне нескольких гейтов вместе
    падали все тесты второго модуля — измерено: 90 errors на
    `-m "tabs or graph or mobile375"`.
    """
    playwright_api = pytest.importorskip(
        "playwright.sync_api", reason="playwright не установлен")
    with playwright_api.sync_playwright() as pw:
        yield pw
