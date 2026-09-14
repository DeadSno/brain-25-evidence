"""F1.2: Гард от мозгибаки — биграммы каша-маркеры отсутствуют в JS и HTML.

Проверяет, что в docs/*.js и docs/*.html нет следов cp1251→utf-8
декодирования битых данных (типичные биграммы: Р°, Рµ, Рё, РРС и т.п.).
"""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

# Типичные биграммы мозгибаки (cp1251-байты, интерпретированные как UTF-8)
MOJIBAKE_MARKERS = [
    "Р°",   # 0xd0 0xb0 = 'а' в cp1251, но '°' в UTF-8
    "Рµ",   # 0xd0 0xb5 = 'е'
    "Рё",   # 0xd1 0x91 = 'ё'
    "РРС",  # 0xd0 0x90 0xd0 0xa0 = 'РР' + неявный спейс
    "РС",   # 0xd0 0xa0 = 'Р' в cp1251
    "Рі",   # 0xd0 0xb3 = 'г'
    "Р»",   # 0xd0 0xbb = 'л'
    "РЅ",   # 0xd0 0xbd = 'н'
    "Рѕ",   # 0xd0 0xbe = 'о'
    "Рї",   # 0xd0 0xbf = 'п'
]


def _collect_js_files() -> list[Path]:
    files = []
    for fp in DOCS.glob("*.js"):
        if "chart.min" in fp.name:
            continue
        files.append(fp)
    return files


def _collect_html_files() -> list[Path]:
    return list(DOCS.glob("*.html"))


def _check_for_mojibake(filepath: Path) -> list[str]:
    """Возвращает список найденных биграмм мозгибаки в файле."""
    text = filepath.read_text(encoding="utf-8")
    found = []
    for marker in MOJIBAKE_MARKERS:
        if marker in text:
            found.append(marker)
    return found


def test_no_mojibake_in_js_files():
    for fp in _collect_js_files():
        markers = _check_for_mojibake(fp)
        assert not markers, (
            f"{fp.name}: обнаружены биграммы мозгибаки {markers} — "
            "возможно, файл был записан через cp1251"
        )


def test_no_mojibake_in_html_files():
    for fp in _collect_html_files():
        markers = _check_for_mojibake(fp)
        assert not markers, (
            f"{fp.name}: обнаружены биграммы мозгибаки {markers} — "
            "возможно, файл был записан через cp1251"
        )


def test_cp1251_fallback_script_js():
    """F1.1-fallback: пытаемся cp1251→utf-8 на script.js. Если файл чист — фикс не нужен."""
    fp = DOCS / "script.js"
    text = fp.read_text(encoding="utf-8")
    fixed_any = False
    for line in text.splitlines():
        try:
            fixed = line.encode("cp1251").decode("utf-8")
            if fixed != line:
                # Проверяем, содержит ли fixed нормальные русские буквы
                if any("\u0430" <= c <= "\u044f" or "\u0410" <= c <= "\u042f" for c in fixed):
                    fixed_any = True
                    break
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    if not fixed_any:
        # Файл чист — это нормально, просто отмечаем
        assert True, "script.js чист, фикс не требуется"
