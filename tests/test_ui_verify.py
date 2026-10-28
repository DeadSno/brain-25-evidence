"""Запуск scripts/ui_verify.py из pytest (QA_AUDIT P1).

232 строки визуальных проверок (анимации, отступы, порядок секций, битые
якоря) живут в scripts/ и не импортируются тестами напрямую.

v5.6.5: скрипт запускается ПОДПРОЦЕССОМ. Раньше main() вызывался в том же
процессе, а скрипт открывает свой `sync_playwright()` — в полном прогоне это
конфликтовало с сессионной фикстурой `playwright_instance` и падало с
`Playwright Sync API inside the asyncio loop` (см. tests/test_e2e_smoke.py).

Запуск:    python -m pytest -q -m e2e
Скрипт поднимает свой http.server на :8123 и Chromium.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.e2e

SCRIPT = ROOT / "scripts" / "ui_verify.py"


def test_ui_verify():
    """Визуальная проверка UI: отступы, анимации, контрастность секций."""
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
        f"ui_verify.py вернул {proc.returncode}\n"
        f"--- stdout ---\n{proc.stdout[-4000:]}\n"
        f"--- stderr ---\n{proc.stderr[-4000:]}"
    )
