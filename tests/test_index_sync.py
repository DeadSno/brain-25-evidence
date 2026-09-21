"""Проверка, что data_index.json синхронизирован с data.json.

Если data.json обновился, а index — нет, тест падает.
Фикс: python scripts/build_index.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_index_sync():
    """data_index.json == проекция data.json по INDEX_FIELDS."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_index.py"), "--check"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"data_index.json рассинхронизирован с data.json.\n"
        f"Запусти: python scripts/build_index.py\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )