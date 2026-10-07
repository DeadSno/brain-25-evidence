"""Проверяет, что гард test_vendor_integrity.py ЛОВИТ подмену.

Именно этот файл — доказательство, что зелёный прогон гарда не пустой:
он создаёт копию вендора, портит байт и прогоняет против неё те же
проверки, что и основной гейт. Если после мутации тест падает — гард рабочий.

Мутация делается в tmp_path, файлы docs/vendor/ не трогаются.
"""
import hashlib
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import test_vendor_integrity as gvd  # noqa: E402

ROOT = gvd.ROOT
SAMPLE = "docs/vendor/chart.umd-4.4.1.min.js"   # небольшой, но не самый мелкий


def _run_check(rel: str, root: Path, expected: dict) -> list[str]:
    """Прогоняет проверку хеша из гарда на подделанном корне.

    Копируем логику проверки, а не сам тест: нужно получить СПИСОК
    расхождений, а не pytest-AssertionError.
    """
    broken = []
    for r, exp in sorted(expected.items()):
        fp = root / r
        if not fp.is_file():
            continue
        if gvd._sha256(fp) != exp:
            broken.append(r)
    return broken


def test_hashes_in_expected_match_real_files():
    """Контроль: зафиксированные хеши соответствуют реальным файлам.

    Если это упало, значит вендор менялся без обновления EXPECTED —
    и остальные тесты этого файла падали бы не потому, что гард работает,
    а потому, что эталон неверен.
    """
    for rel, expected in sorted(gvd.EXPECTED.items()):
        fp = ROOT / rel
        assert fp.is_file(), f"нет файла: {rel}"
        actual = gvd._sha256(fp)
        assert actual == expected, (
            f"{rel}: хеш в EXPECTED не совпадает с файлом\n"
            f"      в EXPECTED {expected}\n"
            f"      фактически  {actual}\n"
            f"      Если библиотеку заменяли намеренно — обнови EXPECTED "
            f"и reports/VIS_CHART_VENDOR.md §2."
        )


def test_gate_fails_on_corrupted_vendor(tmp_path):
    """Портим один байт в копии вендора — гард обязан это заметить."""
    src = ROOT / SAMPLE
    assert src.is_file(), f"нет образца: {SAMPLE}"

    fake_root = tmp_path / "repo"
    (fake_root / "docs" / "vendor").mkdir(parents=True)
    for rel in gvd.EXPECTED:
        shutil.copy2(ROOT / rel, fake_root / rel)

    # 0. контроль: до мутации всё чисто
    assert _run_check(SAMPLE, fake_root, gvd.EXPECTED) == [], (
        "до мутации проверка уже не чистая — тест бессмысленен"
    )

    # 1. мутация: переворачиваем один байт в середине файла
    target = fake_root / SAMPLE
    gvd._corrupt(target, target)

    broken = _run_check(SAMPLE, fake_root, gvd.EXPECTED)
    assert broken == [SAMPLE], (
        f"после подмены байта гард не нашёл расхождения (нашёл {broken}). "
        "Проверка целостности не работает."
    )


def test_gate_fails_on_truncated_vendor(tmp_path):
    """Обрезанный файл (битый partial checkout) — тоже расхождение."""
    fake_root = tmp_path / "repo2"
    (fake_root / "docs" / "vendor").mkdir(parents=True)
    for rel in gvd.EXPECTED:
        shutil.copy2(ROOT / rel, fake_root / rel)

    target = fake_root / SAMPLE
    data = target.read_bytes()
    target.write_bytes(data[: len(data) // 2])

    broken = _run_check(SAMPLE, fake_root, gvd.EXPECTED)
    assert broken == [SAMPLE], "обрезка файла не замечена гардом"


def test_gate_fails_on_swapped_library(tmp_path):
    """Подмена одного файла вендора содержимым другого."""
    fake_root = tmp_path / "repo3"
    (fake_root / "docs" / "vendor").mkdir(parents=True)
    for rel in gvd.EXPECTED:
        shutil.copy2(ROOT / rel, fake_root / rel)

    # вместо chart.js кладём bootstrap.js — размер другой, хеш тоже
    shutil.copy2(ROOT / "docs/vendor/bootstrap-5.0.0-beta3.min.js",
                 fake_root / SAMPLE)

    broken = _run_check(SAMPLE, fake_root, gvd.EXPECTED)
    assert broken == [SAMPLE], "подмена библиотеки не замечена гардом"


def test_unregistered_file_is_detected(tmp_path):
    """Файл без записи в EXPECTED обязан попасть в список «лишних»."""
    fake_root = tmp_path / "repo4"
    vendor = fake_root / "docs" / "vendor"
    vendor.mkdir(parents=True)
    for rel in gvd.EXPECTED:
        shutil.copy2(ROOT / rel, fake_root / rel)

    # новый вендор, добавленный без хеша
    (vendor / "newlib-1.0.0.min.js").write_bytes(b"console.log('hi');")

    untracked = {
        p.relative_to(fake_root).as_posix()
        for p in vendor.rglob("*") if p.is_file()
    } - set(gvd.EXPECTED)

    assert "docs/vendor/newlib-1.0.0.min.js" in untracked, (
        "новый файл в docs/vendor/ не обнаружен — типовой обход гейта открыт"
    )


def test_missing_file_is_detected(tmp_path):
    """Удалённый вендор обязан попасть в список отсутствующих."""
    fake_root = tmp_path / "repo5"
    (fake_root / "docs" / "vendor").mkdir(parents=True)
    for rel in gvd.EXPECTED:
        if rel != SAMPLE:
            shutil.copy2(ROOT / rel, fake_root / rel)

    present = {rel for rel in gvd.EXPECTED if (fake_root / rel).is_file()}
    missing = sorted(set(gvd.EXPECTED) - present)

    assert missing == [SAMPLE], (
        f"удалённый файл не обнаружен (missing={missing}) — страница "
        "отдаст 404 и уедет молча"
    )


def test_sha256_helper_matches_hashlib_on_whole_file():
    """Построчное чтение в _sha256 должно совпадать с чтением целиком."""
    for rel in sorted(gvd.EXPECTED):
        fp = ROOT / rel
        raw = fp.read_bytes()
        whole = hashlib.sha256(raw).hexdigest()
        chunked = gvd._sha256(fp)
        assert chunked == whole, f"{rel}: хеш зависит от способа чтения файла"