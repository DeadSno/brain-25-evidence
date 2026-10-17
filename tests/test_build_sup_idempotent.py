"""Идемпотентность scripts/build_sup.py (F-28, QA-P1-02).

Заявление в докстринге сборщика — «Идемпотентен: повторный запуск даёт
байт-в-байт тот же результат» — не было чем подтверждено. Проверки на
идемпотентность в проекте нет, а руками такие вещи не выглядят: сборщик
перезаписывает файлы всегда (в нём нет ни одного `exists()`), и если
порядок карточек определяется порядком ключей в data.json, то страница
будет «прыгать» при каждом несвязанном дополнении данных — и это
заметят только по diff на 131 странице.

Проверка построена на `--out`: сборка идёт во временный каталог, байты
сравниваются между прогонами, рабочее дерево не трогается.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_sup.py"
COMMITTED = ROOT / "docs" / "sup"

pytestmark = pytest.mark.snapshot_data


def _run_build(out_dir: Path) -> None:
    """Собрать каталог sup целиком в out_dir.

    Каталог создаём сами: `--out` в сборщике не разворачивает дерево
    (`path.write_bytes` без `mkdir`), и без этого первый же файл падает
    с FileNotFoundError. В штатной сборке это незаметно — `docs/sup`
    в репозитории уже есть.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--out", str(out_dir)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"сборка в {out_dir} упала с кодом {proc.returncode}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def _digests(root: Path) -> dict[str, str]:
    """sha256 каждой страницы, ключ — путь относительно каталога."""
    return {
        str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*.html"))
    }


@pytest.fixture(scope="module")
def two_builds(tmp_path_factory) -> tuple[dict[str, str], dict[str, str]]:
    """Две независимые сборки — эталон для сравнения «прогон с прогоном»."""
    first = tmp_path_factory.mktemp("build1") / "sup"
    second = tmp_path_factory.mktemp("build2") / "sup"
    _run_build(first)
    _run_build(second)
    return _digests(first), _digests(second)


def test_build_writes_all_pages(two_builds):
    """Сборка охватывает каталог, а не пару файлов."""
    first, _ = two_builds
    assert len(first) >= 100, f"собрано всего {len(first)} страниц"
    assert "index.html" in first, "нет индексной страницы каталога"


def test_two_builds_are_byte_identical(two_builds):
    """ГЛАВНОЕ: повторный запуск даёт байт-в-байт тот же результат.

    Сравнение идёт по содержимому sha256, а не по mtime и не по факту
    «файл перезаписан»: сборщик переписывает всё всегда, поэтому
    единственный признак идемпотентности — совпадение байтов.
    """
    first, second = two_builds
    only_first = sorted(set(first) - set(second))
    only_second = sorted(set(second) - set(first))
    differ = sorted(k for k in set(first) & set(second) if first[k] != second[k])
    assert not only_first and not only_second and not differ, (
        f"сборка не идемпотентна.\n"
        f"  только в первом прогоне: {only_first[:10]}\n"
        f"  только во втором: {only_second[:10]}\n"
        f"  различаются байтами: {differ[:10]}\n"
        f"  всего расхождений: {len(only_first) + len(only_second) + len(differ)}"
    )


def test_build_matches_committed_pages(two_builds):
    """Собранные страницы совпадают с лежащими в репозитории.

    Без этого идемпотентность была бы самооценкой: сборка стабильна сама
    по себе, но не совпадает с тем, что закоммичено, и расхождение
    обнаружится только при следующей сборке — как diff на 131 файл.
    """
    if not COMMITTED.is_dir():
        pytest.skip(f"нет каталога {COMMITTED}")
    built, _ = two_builds
    committed = _digests(COMMITTED)
    drift = sorted(
        k for k in set(built) | set(committed)
        if built.get(k) != committed.get(k)
    )
    assert not drift, (
        f"сборка разошлась с закоммиченным на {len(drift)} страницах из "
        f"{len(set(built) | set(committed))}:\n  " + "\n  ".join(drift[:20])
        + ("\n  …" if len(drift) > 20 else "")
    )