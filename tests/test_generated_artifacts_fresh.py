"""DATA-P1-13: tests/test_generated_artifacts_fresh.py

Гейт свежести: закоммиченный артефакт обязан быть побайтово равен тому, что
генератор собирает из ТЕКУЩИХ входных файлов.

Зачем. Замер 2026-10-14: `docs/interactions_graph.json` лежал с 2026-09-18,
а `docs/data.json` менялся трижды после него (`ebf4232`, `59cc0de`, `454b956`).
Страница `docs/interactions.html` показывала 124 ребра при 146 в живых данных
и не сообщала об этом: файл читается `fetch` (interactions.html:1024), отказ
или порча не дают ошибки в консоли — просто неверные числа. Причина в том,
что ни один из 13 генераторов `build_*` не вызывался ни из pre-commit, ни из
CI (в `.github/workflows` они встречаются только как триггеры).

Почему сравнение с пересобранным, а не только mtime. Тест на mtime ловит
правку входа, но не ловит ручную порчу артефакта и не ловит ситуацию «вход
откатили, артефакт нет». Сравнение байтов ловит всё и не требует git: в CI
checkout mtime у всех файлов одинаковый.

Про обход. Этот тест краснеет на любом коммите, который меняет вход, но не
перегенерирует артефакт. Так и задумано, и именно поэтому в pre-commit
генераторы идут СТРОГО ДО прогона pytest (блок «генераторы данных»): к моменту
проверки артефакт уже пересобран, и тест проверяет не «успел ли хук», а
ровно то, что попадёт в коммит.

Живой репозиторий тесты не трогают: генераторы всегда запускаются на копии
в `tmp_path`. Сеть не используется.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


#: Генератор, закоммиченный артефакт, входы относительно ROOT.
#: Входы копируются в tmp-клон; остальное генератору не требуется.
CASES = [
    {
        "name": "interactions_graph",
        "script": "scripts/build_interactions_graph.py",
        "artifact": "docs/interactions_graph.json",
        "inputs": ["docs/data.json"],
        "console": "utf-8",
    },
    {
        "name": "timeseries",
        "script": "scripts/build_timeseries.py",
        "artifact": "docs/timeseries.json",
        "inputs": ["data/timeseries/pubmed.json",
                   "data/timeseries/wiki.json",
                   "data/timeseries/citations.json"],
        "console": "utf-8",
    },
]

#: Минимальный размер артефакта в байтах. Ниже — не «граф», а заглушка:
#: сборка из полного входа даёт десятки килобайт, и на таком размере
#: сравнение байтов ещё ничего не доказывает.
MIN_BYTES = 1024


def _clone(case: dict, root: Path) -> Path:
    """Копия генератора и его входов — ровно та раскладка, которую он ждёт.

    Генераторы берут пути от `Path(__file__).parents[1]`, поэтому раскладка
    повторяет живую: scripts/ рядом с docs/ и data/. Каталог создаётся
    всегда: build_timeseries.py пишет в docs/, не создавая его, — а входы
    лежат в data/, так что docs/ в клоне пуста и должна появиться.
    """
    (root / "scripts").mkdir(parents=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    src = ROOT / case["script"]
    assert src.is_file(), f"нет генератора {case['script']}"
    shutil.copy(src, root / case["script"])
    for rel in case["inputs"]:
        src_input = ROOT / rel
        assert src_input.is_file(), f"нет входа {rel} — тест нечего собирать"
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_input, dst)
    return root


def _rebuild(case: dict, root: Path) -> bytes:
    """Прогнать генератор в клоне и вернуть собранный артефакт.

    console — PYTHONIOENCODING дочернего Python: под cp1251 русские
    сообщения генераторов превращаются в «кракозябры», но код возврата
    остаётся 0, так что на результат это не влияет.
    """
    env = {**os.environ, "PYTHONIOENCODING": case["console"]}
    proc = subprocess.run(
        [sys.executable, str(root / case["script"])],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert proc.returncode == 0, (
        f"{case['script']} упал (rc={proc.returncode}):\n"
        f"{proc.stdout}\n{proc.stderr}"
    )
    out = root / case["artifact"]
    assert out.is_file(), f"{case['script']} не создал {case['artifact']}"
    return out.read_bytes()


def _committed_bytes(case: dict) -> bytes:
    path = ROOT / case["artifact"]
    assert path.is_file(), f"нет {case['artifact']} — страница покажет ошибку загрузки"
    return path.read_bytes()


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_artifact_is_not_truncated(case, tmp_path):
    """Артефакт должен быть заметно больше 1 КБ.

    Отдельно от байтового сравнения: если вход в репозитории обрезан,
    пересборка даст такой же обрезанный результат и сравнение пройдёт.
    """
    raw = _committed_bytes(case)
    assert len(raw) > MIN_BYTES, (
        f"{case['artifact']} — {len(raw)} Б, это не данные, а заглушка"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_artifact_matches_rebuild(case, tmp_path):
    """Главная проверка: закоммиченный файл == свежая сборка из текущих входов."""
    fresh = _rebuild(case, _clone(case, tmp_path / "a"))
    committed = _committed_bytes(case)
    if fresh == committed:
        return
    # Расхождение объясняемо, а не просто «красное»: показываем, что и где.
    hint = ""
    if case["name"] == "interactions_graph":
        a = json.loads(committed.decode("utf-8"))
        b = json.loads(fresh.decode("utf-8"))
        for mode in ("supplements", "drugs"):
            hint += (
                f"\n  {mode}: закоммичено {len(a[mode]['nodes'])} нод / "
                f"{len(a[mode]['edges'])} рёбер, собрано "
                f"{len(b[mode]['nodes'])} / {len(b[mode]['edges'])}"
            )
    raise AssertionError(
        f"{case['artifact']} устарел относительно "
        f"{', '.join(case['inputs'])}.{hint}\n"
        f"Пересобери: python {case['script']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_generator_output_is_deterministic(case, tmp_path):
    """Две сборки из одного входа — байт в байт.

    Таймстемпов и итерации по множествам в обоих генераторах нет, поэтому
    расхождение означает нестабильность: артефакт в репозитории мерцал бы
    сам собой, и каждая пересборка давала бы ложное «устарел».
    """
    first = _rebuild(case, _clone(case, tmp_path / "a"))
    second = _rebuild(case, _clone(case, tmp_path / "b"))
    assert first == second, f"{case['script']} недетерминирован"
