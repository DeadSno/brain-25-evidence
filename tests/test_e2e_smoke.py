"""Запуск scripts/e2e_smoke.py из pytest (QA_AUDIT P1).

556 строк проверок живут в scripts/ и вызываются функцией main().

v5.6.5: скрипт запускается ПОДПРОЦЕССОМ, а не через `from e2e_smoke import
main`. Раньше тест вызывал main() в том же процессе, а скрипт открывает свой
`sync_playwright()`. В полном прогоне сессионная фикстура
`playwright_instance` (tests/conftest.py) уже держит один sync-контекст, и
второй падал с `Error: It looks like you are using Playwright Sync API inside
the asyncio loop` — то есть `pytest -q -m e2e` проходил, а обычный
`pytest -q` падал. Подпроцесс даёт чистый интерпретатор без чужого event loop.

Запуск:    python -m pytest -q -m e2e
           python -m pytest -q tests/test_e2e_smoke.py
Скрипт поднимает свой http.server на :8123 и Chromium.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.e2e

SCRIPT = ROOT / "scripts" / "e2e_smoke.py"


def test_e2e_smoke():
    """Чистый запуск смоука: шапка, фильтры, модалка, тема, глоссарий, ошибки."""
    assert SCRIPT.exists(), f"нет скрипта {SCRIPT}"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert proc.returncode == 0, (
        f"e2e_smoke.py вернул {proc.returncode}\n"
        f"--- stdout ---\n{proc.stdout[-4000:]}\n"
        f"--- stderr ---\n{proc.stderr[-4000:]}"
    )
