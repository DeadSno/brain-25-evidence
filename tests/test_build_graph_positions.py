"""Контракт scripts/build_graph_positions.py (PAGES_REVIEW п.20b).

Проверяет, что graph_positions.json — детерминированная круговая
раскладка, воспроизводимая build_graph_positions.py, и что --check проходит.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_graph_positions.py"
POSITIONS = ROOT / "docs" / "graph_positions.json"
GRAPH_DATA = ROOT / "docs" / "graph_data.json"


def _run(args):
    return subprocess.run(
        [sys.executable, str(BUILD)] + args,
        cwd=ROOT, capture_output=True, text=True,
    )


def _positions() -> dict:
    return json.loads(POSITIONS.read_text(encoding="utf-8"))


def _graph_node_ids() -> list[str]:
    g = json.loads(GRAPH_DATA.read_text(encoding="utf-8"))
    return sorted(n["id"] for n in g["nodes"])


def test_idempotent_check_passes():
    """--check → exit 0 (генератор воспроизводит текущий файл)."""
    proc = _run(["--check"])
    assert proc.returncode == 0, (
        f"--check упал с кодом {proc.returncode}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def test_idempotent_two_runs():
    """Два прогона --check подряд → оба exit 0."""
    for _ in range(2):
        proc = _run(["--check"])
        assert proc.returncode == 0


def test_schema():
    p = _positions()
    assert "_комментарий" in p
    assert "_источники" in p
    layout = p["layouts"]["graph"]
    assert set(layout.keys()) == {"center", "scale", "count", "positions"}
    assert layout["center"] == [0.5, 0.5]
    assert layout["scale"] == 1.0
    positions = layout["positions"]
    assert layout["count"] == len(positions) == 130
    for node_id, pos in positions.items():
        assert set(pos.keys()) == {"nx", "ny", "fixed"}
        assert pos["fixed"] is True
        assert 0.0 <= pos["nx"] <= 1.0, f"{node_id}: nx={pos['nx']}"
        assert 0.0 <= pos["ny"] <= 1.0, f"{node_id}: ny={pos['ny']}"


def test_all_ids_present():
    p = _positions()
    positions = p["layouts"]["graph"]["positions"]
    expected = set(_graph_node_ids())
    assert set(positions.keys()) == expected, (
        f"несоответствие id: missing={expected - set(positions)} "
        f"extra={set(positions) - expected}"
    )


def test_deterministic_circular_formula():
    """nx/ny соответствуют углу 2*pi*i/N при сортировке по id."""
    import math

    p = _positions()
    positions = p["layouts"]["graph"]["positions"]
    node_ids = sorted(positions.keys())
    n = len(node_ids)
    for i, node_id in enumerate(node_ids):
        angle = 2 * math.pi * i / n
        exp_nx = 0.5 + 0.5 * math.cos(angle)
        exp_ny = 0.5 + 0.5 * math.sin(angle)
        pos = positions[node_id]
        # CI-02: генератор пишет значения с round(..., 6), поэтому допуск
        # 1e-6 (полшага округления), а не 1e-9 как до FIX-05.
        assert abs(pos["nx"] - exp_nx) < 1e-6, f"{node_id}: nx mismatch"
        assert abs(pos["ny"] - exp_ny) < 1e-6, f"{node_id}: ny mismatch"


def test_values_are_rounded_to_micro():
    """CI-02: все nx/ny кратны 1e-6.

    Гвард от возврата сырых double: libm на Windows (MSVCRT) и Linux (glibc)
    расходится на 1 ULP, поэтому неокруглённые значения делают
    docs/graph_positions.json невоспроизводимым и роняют --check в CI
    (`Executable`-независимо, проверено запуском 40500055108).
    """
    positions = _positions()["layouts"]["graph"]["positions"]
    bad = []
    for node_id, pos in positions.items():
        for axis in ("nx", "ny"):
            value = pos[axis]
            scaled = value * 1e6
            if abs(scaled - round(scaled)) > 1e-9:
                bad.append(f"{node_id}.{axis}={value!r}")
    assert not bad, (
        f"значения не кратны 1e-6 ({len(bad)} из {len(positions) * 2}): {bad[:5]}"
    )
