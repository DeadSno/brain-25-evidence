"""Тест: hook не блокирует коммит при расхождении слепка с data.json.

Меняет копию data.json так, чтобы test_snapshot_unchanged гарантированно
падал, и проверяет, что pytest с фильтром hook остаётся зелёным.
Живой docs/data.json не трогает — работа идёт через monkeypatch на модуль.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HOOK_FILTER = "not network and not snapshot_data"
SNAP = ROOT / "tests" / "snapshot_data.json"
DATA = ROOT / "docs" / "data.json"


def test_hook_filter_excludes_snapshot():
    """Фильтр hook не отбирает тест слепка."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-m", HOOK_FILTER,
         "--collect-only", "--no-header"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert "test_snapshot" not in out.stdout, (
        "фильтр hook всё ещё собирает test_snapshot"
    )


def test_plain_run_keeps_snapshot():
    """Обычный прогон без фильтра тест слепка НЕ отбрасывает."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only", "--no-header"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert "test_snapshot_unchanged" in out.stdout, (
        "тест слепка пропал из обычного прогона — гейт на мутацию данных выключен"
    )


def test_marker_registered():
    """Маркер snapshot_data объявлен: --strict-markers иначе роняет сборку."""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "snapshot_data:" in ini


def test_hook_mentions_filter():
    """Hook на диске использует ровно тот фильтр, который проверяется выше."""
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    if not hook.exists():
        return  # hook не установлен в этой копии — нечего проверять
    text = hook.read_text(encoding="utf-8", errors="replace")
    assert HOOK_FILTER in text, (
        "pre-commit не исключает snapshot_data — коммит с обновлением данных "
        "заблокируется"
    )


def test_hook_passes_with_diverged_snapshot(tmp_path, monkeypatch):
    """Слепок разошёлся с данными: hook-фильтр зелёный, полный прогон падает."""
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    # Слепок — список карточек. Добавляем лишний элемент, чтобы гарантированно
    # разойтись с data.json, не трогая сами карточки.
    broken = [*snap, {"id": "__probe__", "name": "__probe__"}]
    broken_path = tmp_path / "snapshot_data.json"
    broken_path.write_text(json.dumps(broken, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    import tests.test_snapshot as ts
    monkeypatch.setattr(ts, "SNAP", broken_path)

    # Часть 1: фильтр hook отбирает тест слепка. Считаем через --collect-only,
    # потому что после исключения из файла не остаётся ничего и pytest вернул
    # бы exit 5 («нечего собирать»), а не 0.
    hook_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-m", HOOK_FILTER,
         "--no-header", "--collect-only", str(ts.__file__)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert "test_snapshot_unchanged" not in hook_run.stdout, (
        "hook-фильтр всё же собирает тест слепка — коммит с обновлением данных "
        "будет заблокирован"
    )

    # Часть 2: тот же расхождённый слепок обязан ронять тест при обычном
    # запуске — иначе гейт на мутацию данных выключен по сути.
    # Вызываем функцию напрямую: monkeypatch на модуль виден только в этом
    # процессе, в подпроцессе pytest исполнился бы настоящий tests/snapshot_data.json.
    with pytest.raises(AssertionError, match="слепка"):
        ts.test_snapshot_unchanged()


def test_live_data_untouched():
    """Прогон тестов не изменил живой docs/data.json."""
    assert DATA.exists()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(data) == 130
    assert all("price_date" not in s for s in data)