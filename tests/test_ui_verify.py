"""Запуск scripts/ui_verify.py как теста pytest (QA_AUDIT P1).

232 строки визуальных проверок (гайды, отступы, контраст, скриншоты секций
доверия) лежали в scripts/ и не запускались никогда — по той же причине,
что и e2e_smoke.py: pytest.ini ограничен testpaths = tests.

Тест импортирует main() и вызывает её, поэтому assert'ы внутри скрипта
становятся проверками pytest. Логика не дублируется.

Запуск:    pytest -q -m e2e
По умолчанию e2e исключён (см. pytest.ini addopts).

ВНИМАНИЕ: оба скрипта поднимают свой http.server на ПОРТУ 8123. Запускать их
в одном прогоне можно только последовательно — pytest и так выполняет тесты
в одном процессе, но если запустить два прогона pytest одновременно (например,
`-n auto`), они столкнутся за порт; поэтому проверка занятости порта стоит
в skipif.
"""
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

pytestmark = pytest.mark.e2e

PORT = 8123  # тот же порт, что в scripts/ui_verify.py (BASE = http://localhost:8123)


def _port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return True
    return False


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            b.close()
    except Exception:  # noqa: BLE001 — браузер может быть не установлен
        return False
    return True


@pytest.mark.skipif(_port_busy(PORT), reason=f"порт {PORT} занят — скрипт не сможет поднять свой http.server")
@pytest.mark.skipif(not _chromium_available(), reason="playwright или Chromium не установлены (playwright install chromium)")
def test_ui_verify():
    """Визуальная проверка UI: отступы, контраст, компактность секций."""
    from ui_verify import main

    rc = main()
    assert rc == 0, f"ui_verify вернул код {rc}"
