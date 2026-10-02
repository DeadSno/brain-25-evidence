"""Запуск scripts/e2e_smoke.py как теста pytest (QA_AUDIT P1).

556 строк браузерных проверок лежали в scripts/ с единственной функцией main() и
`if __name__ == "__main__"`. pytest.ini ограничивает testpaths = tests, поэтому
этот единственный уровень тестирования, ловящий регрессии рендеринга, не
запускался НИКОГДА — ни локально, ни в CI.

Тест не переписывает логику: он импортирует main() и вызывает её, поэтому
все ~60 assert внутри скрипта становятся проверками pytest (AssertionError →
FAILED). Дублировать 556 строк было бы худшим вариантом — через месяц они бы
разошлись.

Запуск:    pytest -q -m e2e
           pytest -q tests/test_e2e_smoke.py -m e2e
По умолчанию e2e ИСКЛЮЧЁН через pytest.ini (addopts: -m "not network and not e2e"),
потому что прогон длинный (30+ загрузок страниц, запуск http.server и Chromium)
и CI не ставит браузер: `playwright install chromium` в workflows/tests.yml нет,
поэтому включение e2e по умолчанию уронило бы сборку.
"""
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

pytestmark = pytest.mark.e2e

PORT = 8123  # тот же порт, что в scripts/e2e_smoke.py (BASE = http://localhost:8123)


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
def test_e2e_smoke():
    """Полный браузерный смоук: карточки, модалка, атлас, тема, консольные ошибки."""
    from e2e_smoke import main

    main()  # все проверки внутри — assert; AssertionError превращается в FAILED
