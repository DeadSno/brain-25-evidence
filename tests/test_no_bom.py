"""P27: UTF-8 no BOM only. Проверяет отсутствие BOM в HTML/CSS/JS.

Правило зафиксировано в docs/dev/AGENTS.md (раздел Encoding) и в NFR:
канон — 0 BOM. Проверка нужна потому, что нарушение невидимо: правка
через инструмент молча снимает BOM, а **второй** BOM тем хуже — перед
<!DOCTYPE> он превращается в символьный токен, из-за чего парсер не
распознаёт doctype и страница уходит в quirks mode. Внешне это
выглядит как «страница просто стала на 24 px ниже», и по скриншоту
отличить дефект от нормы нельзя.

Разбор случая — reports/GLOSSARY_BOM_INVESTIGATION.md:
8 страниц с двойным BOM рендерились в quirks mode, где ячейки таблиц
теряли наследованный line-height, body не уважал max-width, а
meta viewport уезжал в body и игнорировался.
"""
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
BOM = b"\xef\xbb\xbf"

PATTERNS = ("*.html", "sup/*.html", "*.js", "*.css")


def _files(patterns=PATTERNS):
    for pattern in patterns:
        for f in sorted(DOCS.glob(pattern)):
            if f.is_file():
                yield f


def _rel(f: Path) -> str:
    return f.relative_to(DOCS.parent).as_posix()


def test_no_bom_in_docs():
    offenders = [str(_rel(f)) for f in _files() if f.read_bytes()[:3] == BOM]
    assert not offenders, (
        f"BOM найден в {len(offenders)} файлах — нарушение P27 "
        f"(«UTF-8 no BOM only»):\n" + "\n".join(f"  {f}" for f in offenders)
    )


def test_no_double_bom_in_docs():
    """Двойной BOM ломает разбор документа (quirks mode)."""
    offenders = []
    for f in _files(("*.html", "sup/*.html")):
        raw = f.read_bytes()
        n = 0
        i = 0
        while raw[i:i + 3] == BOM:
            n += 1
            i += 3
        if n >= 2:
            offenders.append(f"{_rel(f)} ({n} BOM)")
    assert not offenders, (
        f"Двойной BOM в {len(offenders)} HTML — парсер не распознаёт "
        f"<!DOCTYPE>, страница рендерится в quirks mode:\n"
        + "\n".join(f"  {f}" for f in offenders)
    )


def test_doctype_not_shadowed_in_docs():
    """Страница обязана начинаться с <!doctype.

    Стоит рядом с проверкой BOM по практической причине: двойной BOM
    не ломает файл, а **отменяет doctype** — парсер уходит в quirks
    mode, и страница выглядит просто «чуть ниже», без явной ошибки.
    Тест ловит именно этот класс повреждения.

    Файлы, которые не являются страницами (например
    google<id>.html с токеном верификации), пропускаются: doctype
    требуется только настоящим документам.
    """
    broken = []
    for f in _files(("*.html", "sup/*.html")):
        raw = f.read_bytes()
        if b"<html" not in raw.lower():
            continue                      # не страница (токен верификации)
        if not raw[:64].lstrip().lower().startswith(b"<!doctype html"):
            broken.append(_rel(f))
    assert not broken, (
        f"Страница не начинается с <!doctype html ({len(broken)}):\n"
        + "\n".join(f"  {f}" for f in broken)
    )


def test_bom_scan_covers_everything_the_project_ships():
    """Скан не должен молча пропускать новые типы файлов."""
    checked = {f.suffix for f in _files()}
    assert checked == {".html", ".js", ".css"}, (
        f"Набор расширений изменился: {sorted(checked)}. Если появился "
        f"новый тип (например .json в docs/), добавь его в PATTERNS — "
        f"иначе проверка P27 останется слепой к нему."
    )