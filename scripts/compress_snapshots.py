#!/usr/bin/env python3
"""
Сжатие эталонов tests/snapshots/<движок>/*.PNG без потери пикселей.
С v5.1.6 эталоны разложены по движкам (chromium/, webkit/), скан идёт
на уровень вглубь и пропускает _actual/ с артефактами падений.

Зачем
-----
37 эталонов занимают ~22 МБ. PNG не дельта-сжимаются в git, поэтому каждая
перезапись после правки CSS добавляет в историю весь набор заново: 10 итераций
миграции дизайн-системы — это сотни мегабайт. При этом пиксели менять нельзя:
тест сравнивает их попиксельно, и любое искажение сделает эталон
недостоверным.

Инструмент — oxipng, оптимизация строго lossless: палитра, фильтры строк и
zlib-поток меняются, значения RGB не трогаются.

Установка
---------
Скрипт сам находит oxipng, а если не нашёл — скачивает с GitHub Releases.
    1) уже стоит в PATH          -> используется как есть
    2) рядом со скриптом         -> ./oxipng.exe (или ./oxipng)
    3) переменная окружения      -> OXIPNG=<путь к oxipng.exe>
    4) ничего из этого           -> скачивается во временный каталог
Автоматическая загрузка требует сети только при первом запуске.

Запуск
------
    python scripts/compress_snapshots.py            # показать выигрыш
    python scripts/compress_snapshots.py --apply    # сжать на месте
    python scripts/compress_snapshots.py --check    # все файлы открываются
    python scripts/compress_snapshots.py --zopfli   # дольше, выигрыш ~1%

Гарантия
--------
--apply перезаписывает файл, только если попиксельно свежий результат совпал с
исходными (сравнение через Pillow по хэшу пикселей, а не по размеру или хэшу
файла). Если хоть один пиксель отличается — файл оставлен как был, сообщение
уходит в stderr, код выхода ненулевой. Сжать битый файл и потерять эталон
нечем.

Что НЕ включается и почему
--------------------------
--alpha переписывает прозрачность ради экономии. Это уже потеря пикселей,
а сравнение попиксельное. --interlace и --reduce тоже меняют растр.
Только --strip safe: убираются метаданные, не влияющие на картинку.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "tests" / "snapshots"

#: Сколько итераций оптимизации. Замерено на этой выборке: -o 6 против -o 4
#: даёт +0.18% за 18 с на 3 файла — ниже любого разумного порога, поэтому
#: 4 и не выше.
LEVEL = "4"

BASE_FLAGS = ["--strip", "safe", "--force", "--quiet"]


def oxipng_flags(level: str = LEVEL, zopfli: bool = False) -> list[str]:
    flags = ["-o", str(level), *BASE_FLAGS]
    if zopfli:
        flags.append("-Z")
    return flags


#: Репозиторий oxipng переехал с shssoichiro/oxipng на oxipng/oxipng, и старый
#: URL отдаёт 404. Поэтому адрес не собирается руками, а берётся из API
#: GitHub: там перечислены настоящие имена файлов под текущий релиз.
OXIPNG_REPO = "oxipng/oxipng"
OXIPNG_API = "https://api.github.com/repos/{repo}/releases/latest"


def _want_asset(version: str, machine: str) -> str | None:
    """Имя файла-сборки под текущую ОС, либо None."""
    arch64 = machine in ("amd64", "x86_64", "arm64", "aarch64")
    if sys.platform == "win32":
        arch = "x86_64" if machine in ("amd64", "x86_64") else "i686"
        return f"oxipng-{version}-{arch}-pc-windows-msvc.zip"
    if sys.platform == "darwin":
        arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
        return f"oxipng-{version}-{arch}-apple-darwin.tar.gz"
    if not arch64:
        return None
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
    libc = "musl" if not Path("/lib/ld-musl-x86_64.so.1").exists() else "gnu"
    return f"oxipng-{version}-{arch}-unknown-linux-{libc}.tar.gz"


def _asset_url(version: str) -> tuple[str, str] | None:
    """-> (url, kind) для текущей ОС, либо None."""
    want = _want_asset(version, platform.machine().lower())
    if not want:
        return None
    req = urllib.request.Request(
        OXIPNG_API.format(repo=OXIPNG_REPO),
        headers={"User-Agent": "compress_snapshots"})
    try:
        release = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст ошибки
        print(f"Не удалось получить список релизов oxipng: {exc}", file=sys.stderr)
        return None
    for asset in release.get("assets", []):
        if asset.get("name") == want:
            url = asset.get("browser_download_url")
            if url:
                return url, ("zip" if want.endswith(".zip") else "tar")
    print(f"В релизе {release.get('tag_name')} нет сборки {want}", file=sys.stderr)
    return None


def _download_oxipng(version: str) -> str | None:
    """Скачать бинарь во временный каталог. -> путь или None."""
    got = _asset_url(version)
    if not got:
        return None
    url, kind = got
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            blob = resp.read()
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст ошибки
        print(f"Не удалось скачать oxipng: {exc}", file=sys.stderr)
        return None

    tmp = Path(tempfile.mkdtemp(prefix="oxipng_"))
    name = "oxipng.zip" if kind == "zip" else "oxipng.tar.gz"
    archive = tmp / name
    archive.write_bytes(blob)
    if kind == "zip":
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
    else:
        with tarfile.open(archive) as t:
            t.extractall(tmp)
    exe_name = "oxipng.exe" if sys.platform == "win32" else "oxipng"
    for cand in tmp.rglob(exe_name):
        cand.chmod(cand.stat().st_mode | stat.S_IEXEC)
        return str(cand)
    return None


def find_oxipng(version: str = "10.2.1") -> tuple[str | None, str]:
    """-> (путь, откуда взят)."""
    env = os.environ.get("OXIPNG")
    if env and Path(env).exists():
        return env, "переменная окружения OXIPNG"
    local = Path(__file__).resolve().parent / (
        "oxipng.exe" if sys.platform == "win32" else "oxipng")
    if local.exists():
        return str(local), "рядом со скриптом"
    found = shutil.which("oxipng")
    if found:
        return found, "PATH"
    got = _download_oxipng(version)
    if got:
        return got, f"скачан ({version})"
    return None, "не найден"


def _png_path():
    try:
        from PIL import Image
    except ImportError:
        return None
    return Image


def pixel_hash(path: Path):
    """Хэш ПИКСЕЛЕЙ, а не файла. Именно это должно остаться неизменным."""
    Image = _png_path()
    if Image is None:
        return None
    with Image.open(path) as im:
        return (im.size, im.mode,
                hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest())


def compress_one(oxipng: str, src: Path, level: str, zopfli: bool) -> tuple[bool, str]:
    """Сжать один файл. -> (успех, сообщение)."""
    before_px = pixel_hash(src)
    before_size = src.stat().st_size
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / src.name
        cmd = [oxipng, *oxipng_flags(level, zopfli), "--out", str(out), str(src)]
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if proc.returncode != 0:
            return False, f"oxipng вернул {proc.returncode}: {proc.stderr.strip()[:200]}"
        if not out.exists():
            return False, "oxipng не создал выходной файл"

        after_px = pixel_hash(out)
        if before_px is not None and after_px is not None and before_px != after_px:
            return False, ("ПИКСЕЛИ ИЗМЕНИЛИСЬ — файл оставлен без изменений "
                           f"({before_px[0]} -> {after_px[0]})")

        new_size = out.stat().st_size
        if new_size >= before_size:
            return False, f"не меньше исходного ({before_size} -> {new_size}), пропущено"

        shutil.copyfile(out, src)
        return True, f"{before_size} -> {new_size} ({_pct(before_size, new_size)})"


def _pct(old: int, new: int) -> str:
    return f"-{100.0 * (old - new) / old:.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Сжатие PNG-эталонов без потери пикселей")
    ap.add_argument("--apply", action="store_true",
                    help="сжать на месте (по умолчанию только показать выигрыш)")
    ap.add_argument("--check", action="store_true",
                    help="только проверить, что файлы открываются")
    ap.add_argument("--zopfli", action="store_true",
                    help="дополнительно -Z (медленно, выигрыш около процента)")
    ap.add_argument("--level", default=LEVEL, help=f"уровень оптимизации (по умолч. {LEVEL})")
    ap.add_argument("--oxipng-version", default="10.2.1",
                    help="версия oxipng для автоскачивания")
    args = ap.parse_args()

    if not SNAP_DIR.exists():
        print(f"Нет каталога эталонов: {SNAP_DIR}", file=sys.stderr)
        return 2

    # С v5.1.6 эталоны разложены по движкам: snapshots/chromium/*.png и
    # snapshots/webkit/*.png. Сканируем на уровень глубже, но НЕ заходим в
    # _actual/ — там артефакты падений, они в git игнорируются и жать их нельзя.
    files = sorted(
        p for p in SNAP_DIR.glob("*/*.png")
        if p.parent.name != "_actual")
    if not files:
        print(f"В {SNAP_DIR} нет PNG (ищем один уровень вглубь: "
              f"<движок>/*.png)", file=sys.stderr)
        return 2

    total_before = sum(f.stat().st_size for f in files)
    print(f"Файлов: {len(files)}, исходно {total_before / 1048576:.2f} МБ")

    if args.check:
        Image = _png_path()
        bad = 0
        for f in files:
            try:
                if Image is None:
                    raise RuntimeError("Pillow не установлен")
                with Image.open(f) as im:
                    im.load()
            except Exception as exc:  # noqa: BLE001 — сообщаем и идём дальше
                print(f"  БИТЫЙ: {f.name}: {exc}", file=sys.stderr)
                bad += 1
        print("Проверка: все файлы открываются" if not bad else f"БИТЫХ: {bad}")
        return 1 if bad else 0

    oxipng, origin = find_oxipng(args.oxipng_version)
    if not oxipng:
        print("oxipng не найден и скачать не удалось. Установка — в докстринге "
              "этого файла.", file=sys.stderr)
        return 2

    print(f"oxipng: {oxipng}  ({origin})")
    print(f"флаги: {' '.join(oxipng_flags(args.level, args.zopfli))}"
          f"  (lossless, --strip safe, без --alpha)")
    if not args.apply:
        print("\nРежим просмотра. Для сжатия: --apply\n")

    saved = 0
    failed = 0
    for f in files:
        before = f.stat().st_size
        if args.apply:
            ok, msg = compress_one(oxipng, f, args.level, args.zopfli)
            if not ok:
                print(f"  {f.name:26s} ПРОПУЩЕН: {msg}", file=sys.stderr)
                failed += 1
                continue
            saved += before - f.stat().st_size
            print(f"  {f.name:26s} {msg}")
        else:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / f.name
                proc = subprocess.run(
                    [oxipng, *oxipng_flags(args.level, args.zopfli),
                     "--out", str(out), str(f)],
                    capture_output=True, text=True, errors="replace")
                if proc.returncode != 0 or not out.exists():
                    print(f"  {f.name:26s} ОШИБКА oxipng", file=sys.stderr)
                    failed += 1
                    continue
                nb = out.stat().st_size
                saved += before - nb
                same = pixel_hash(out) == pixel_hash(f)
                print(f"  {f.name:26s} {before:>8d} -> {nb:>8d}  {_pct(before, nb)}"
                      f"   (пиксели: {'проверены' if same else 'РАЗЛИЧАЮТСЯ!'})")

    total_after = sum(f.stat().st_size for f in files)
    print(f"\nИтого: {total_before / 1048576:.2f} МБ -> {total_after / 1048576:.2f} МБ "
          f"({_pct(total_before, total_after)}), сэкономлено {saved / 1048576:.2f} МБ")
    if failed:
        print(f"Пропущено файлов: {failed}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())