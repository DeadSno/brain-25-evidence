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

v5.6.3: два расширения покрытия (ROADMAP #46)
-------------------------------------------
1. **Обход стал рекурсивным.** Раньше сканировались только docs/*.html,
   docs/sup/*.html, docs/*.js, docs/*.css — верхний уровень плюс sup.
   Вне охвата оставались docs/vendor/ (4 файла, включая chart.js и
   bootstrap, которые реально грузятся страницами), docs/dev/ (9),
   docs/adr/ (6), docs/briefs/ (12). Правило «канон — 0 BOM» на
   отгружаемый вендор не распространялось.

2. **Добавлены типы файлов, которые читает браузер.** .json (21),
   .webmanifest, .xml (sitemap и feed), .txt, .md, .yaml, .bpmn.
   Раньше их не видел даже self-check (test_bom_scan_covers_
   everything_the_project_ships), который проверял ровно тот же
   список, который и писал, — то есть был тавтологией: покрытие
   изменить было нечем. Теперь self-check сверяется с тем, что
   реально лежит в docs/, и любой новый тип обязан быть либо
   объявлен текстовым, либо попасть в KNOWN_BINARY.

Сам тест прошёл при первом же прогоне с расширенным охватом: BOM в
docs/ нет ни в одном файле, включая вендор.
"""
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
BOM = b"\xef\xbb\xbf"

#: Типы файлов, которые браузер или его инструменты читают как текст.
#: BOM в каждом из них ломает разбор: JSON.parse ругается на U+FEFF,
#: XML-парсеры считают документ битым, шаблон получает \ufeff в тексте.
TEXT_SUFFIXES = {
    ".html", ".css", ".js",
    ".json", ".webmanifest", ".xml", ".txt", ".md", ".yaml", ".bpmn",
}

#: Типы, где BOM невозможен по построению — проверять бессмысленно.
KNOWN_BINARY = {".png", ".woff2"}

#: Файлы без расширения. pathlib у `.nojekyll` возвращает suffix == '',
#: потому что имя целиком начинается с точки, — такие имена проверяются
#: отдельно, иначе self-check ругался бы на пустую строку.
KNOWN_DOTFILES = {".nojekyll"}

#: Хвосты мусорных бэкапов (13 файлов *.bak-<метка>). Их расширение
#: уникально для каждого файла, поэтому в набор они не попадают.
#: Список — предмет junk guard, а не проверки кодировки.
JUNK_MARKER = ".bak-"

#: Служебные файлы верификации поисковых систем. Страницами не являются,
#: но, в отличие от токена Google (одна строка без <html>), содержат
#: <html>, поэтому общий отсев «не страница» их не ловит — их приходится
#: называть явно. Ни <!doctype, ни <meta charset> в них нет и быть не
#: может: содержимое выдано поисковиком дословно, менять его нельзя
#: (задание владельца 16.10.2026).
VERIFICATION_FILES = {"yandex_cc2e3cf2ee185b01.html"}


def _has_bom(f: Path) -> bool:
    """Читает только первые 3 байта.

    Раньше было f.read_bytes()[:3] — это читает файл ЦЕЛИКОМ, чтобы
    отбросить хвост. На docs/data.json и соседях это десятки мегабайт
    на каждый прогон ради трёх байт.
    """
    with f.open("rb") as fh:
        return fh.read(3) == BOM


def _files(suffixes=None):
    wanted = TEXT_SUFFIXES if suffixes is None else suffixes
    for f in sorted(DOCS.rglob("*")):
        if not f.is_file():
            continue
        if JUNK_MARKER in f.name:
            continue
        if f.suffix.lower() in wanted:
            yield f


def _rel(f: Path) -> str:
    return f.relative_to(DOCS.parent).as_posix()


def test_no_bom_in_docs():
    offenders = [str(_rel(f)) for f in _files() if _has_bom(f)]
    assert not offenders, (
        f"BOM найден в {len(offenders)} файлах — нарушение P27 "
        f"(«UTF-8 no BOM only»):\n" + "\n".join(f"  {f}" for f in offenders)
    )


def test_no_double_bom_in_docs():
    """Двойной BOM ломает разбор документа (quirks mode)."""
    offenders = []
    for f in _files({".html"}):
        with f.open("rb") as fh:
            raw = fh.read(4096)
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
    требуется только настоящим документам. Токен Google отсеивается
    сам — в нём нет тега <html>; файл верификации Яндекса этот тег
    содержит, поэтому назван явно в VERIFICATION_FILES.
    """
    broken = []
    for f in _files({".html"}):
        with f.open("rb") as fh:
            raw = fh.read(4096)
        if b"<html" not in raw.lower():
            continue                      # не страница (токен верификации)
        if f.name in VERIFICATION_FILES:
            continue                      # файл верификации (не страница)
        if not raw[:64].lstrip().lower().startswith(b"<!doctype html"):
            broken.append(_rel(f))
    assert not broken, (
        f"Страница не начинается с <!doctype html ({len(broken)}):\n"
        + "\n".join(f"  {f}" for f in broken)
    )


def test_bom_scan_covers_everything_the_project_ships():
    """Каждый тип файла в docs/ либо сканируется, либо объявлен бинарным.

    До v5.6.3 проверка сравнивала охват с константой, которую сама же
    и использовала для скана, — то есть всегда проходила и не могла
    упасть. Теперь эталон берётся с диска.
    """
    present: set[str] = set()
    dotfiles: set[str] = set()
    for f in DOCS.rglob("*"):
        if not f.is_file() or JUNK_MARKER in f.name:
            continue
        (dotfiles.add(f.name) if not f.suffix else present.add(f.suffix.lower()))

    unscanned = sorted(present - TEXT_SUFFIXES - KNOWN_BINARY)
    assert not unscanned, (
        f"Типы файлов в docs/, которые скан BOM не покрывает: "
        f"{', '.join(unscanned)}. Если тип читается как текст — добавь его "
        f"в TEXT_SUFFIXES. Если это бинарный файл — в KNOWN_BINARY, "
        f"чтобы решение было записано, а не подразумевалось."
    )

    unknown_dotfiles = sorted(dotfiles - KNOWN_DOTFILES)
    assert not unknown_dotfiles, (
        f"Файлы без расширения, которые скан BOM не покрывает: "
        f"{', '.join(unknown_dotfiles)}. Добавь их в KNOWN_DOTFILES, "
        f"если они бинарные."
    )

    # Обратная проверка: объявленный текстовый тип должен реально
    # существовать, иначе скан тихо пустеет после удаления папки.
    absent = sorted(t for t in TEXT_SUFFIXES if not any(
        f.suffix.lower() == t for f in DOCS.rglob("*") if f.is_file()))
    assert not absent, (
        f"TEXT_SUFFIXES объявляет типы, которых в docs/ нет: "
        f"{', '.join(absent)}. Убери их или добавь файлы."
    )


def test_bom_scan_actually_reads_the_expected_number_of_files():
    """Страховка от молчаливого схлопывания охвата в ноль.

    Тот же класс ошибок, что test_no_orphan_classes.py страхуется числом
    страниц: если rglob перестанет что-то находить, все три проверки
    выше станут зелёными, не проверив ни одного файла. Замер 2026-10-12:
    237 файлов (было 158 при нерекурсивном обходе). Нижняя граница 200
    означает: падение ниже неё — обход сломан, а не файлы удалили.
    """
    scanned = list(_files())
    n = len(scanned)
    assert n >= 200, (
        f"Скан BOM прочитал {n} файлов, ожидалось не меньше 200. "
        f"Обход, скорее всего, сломан — проверки выше в этом случае "
        f"зелёные вхолостую."
    )
    # Отдельно: вендор обязан быть в охвате. Именно его не видел
    # прежний нерекурсивный вариант, и именно он грузится страницами.
    assert any(f.parent.name == "vendor" for f in scanned), (
        "docs/vendor/ не попал в скан. Прежний вариант PATTERNS был "
        "нерекурсивным и вендор не проверял вообще."
    )


def test_charset_declaration_precedes_any_fetchable_element():
    """Объявление кодировки должно идти раньше того, что её требует.

    SEO-P2-02, найдено аудитом: в 9 страницах `<script defer
    src="version.js">` стоял ВЫШЕ `<meta charset="utf-8">` — то есть
    браузер уже начал выбирать кодировку по содержимому, а объявление
    приходило следом.

    Почему это вообще про кодировку, а не про порядок тегов: браузер
    определяет кодировку по BOM, затем по HTTP-заголовку, затем по
    meta. Объявление в meta работает только в первых 1024 байтах
    документа. Здесь оно стояло на ~40 байте, то есть формально
    укладывалось, и страница выглядела нормально — но контракт
    «кодировка объявлена до того, как начался разбор» был нарушен, и
    любая правка в этих строках (например добавление локализованного
    имени файла скрипта) могла его сломать уже заметно.

    Проверка формулируется шире частного случая: charset обязан
    предшествовать ЛЮБОМУ элементу, который браузер начинает
    разбирать до его объявления, — script, link, style, title.

    Файл верификации Яндекса объявляет кодировку через
    `<meta http-equiv="Content-Type" ...>` — под `<meta charset>` он
    не подходит; отсеивается по VERIFICATION_FILES, как и в проверке
    doctype.
    """
    import re

    charset_re = re.compile(r'<meta\s+charset\s*=', re.I)
    before_re = re.compile(r"<(script|link|style|title)\b", re.I)

    offenders = []
    for f in _files({".html"}):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "<html" not in text.lower():
            continue                      # не страница (токен верификации)
        if f.name in VERIFICATION_FILES:
            continue                      # файл верификации (не страница)
        m = charset_re.search(text)
        if not m:
            offenders.append(f"{_rel(f)} — нет meta charset")
            continue
        early = before_re.search(text, 0, m.start())
        if early:
            offenders.append(
                f"{_rel(f)} — <{early.group(1)}> идёт раньше meta charset"
            )
    assert not offenders, (
        f"Объявление кодировки не первое в <head> ({len(offenders)}):\n"
        + "\n".join(f"  {f}" for f in offenders)
    )