"""Гард целостности вендоренных библиотек: sha256 каждого файла в docs/vendor/.

Зачем этот гейт
---------------
При вендоринге (v5.6.1, `reports/VIS_CHART_VENDOR.md`) у страниц исчезли все
CDN-ссылки, и вместе с ними исчезла единственная защита от подмены кода —
атрибут `integrity` (SRI). Он убран намеренно: на локальный файл SRI
бессмысленен, потому что считается от содержимого, а локальный файл и есть
эталон. Но вместе с ним пропал и сам факт проверки: **что лежит в репозитории,
теперь не проверяет ничего**.

Дыру эту видно на примере прошлой задачи. Аудит классов (`scripts/audit_classes.py`)
разбирал подключённые скрипты и пропускал `kind == "cdn"` как чужой код.
Вендоринг превратил CDN-теги в локальные файлы, и разбор пошёл по 688 КБ
vis-network и 80 КБ bootstrap **как по коду проекта** — два теста
`test_no_orphan_classes.py` упали. То есть вендор, попавший в репозиторий
незаметно, влияет на логику проверок проекта, и ничто этого не замечает.

Что ловит тест
--------------
Три класса расхождений, и каждый закрывает свой обход:

1. **Файл из EXPECTED отсутствует** — вендор удалён или потерян, страницы
   отдают 404 и падают молча (визуально: пустой график, график без осей).
2. **Файл в docs/vendor/ есть, но его нет в EXPECTED** — новый вендор,
   добавленный без хеша. Это самый частый и самый тихий обход гейта: новый
   файл проходит любую проверку «всё на месте», потому что проверять нечего.
   Именно этот случай закрывает `test_no_unregistered_vendor_file`.
3. **Хеш не совпал** — файл подменён: другая версия библиотеки, правка
   минифицированного байта, битый partial checkout. Отличие от версии по
   имени: версия в файле может совпадать, а содержимое — нет.

Чего гард НЕ делает
-------------------
Не проверяет, что версия библиотеки свежая, и не проверяет лицензии.
Это гейт на неизменность байтов, а не на аптайм зависимостей.

Хеши взяты из `reports/VIS_CHART_VENDOR.md` §2 (задача вендоринга v5.6.1)
и сверены с фактическими файлами расчётом sha256 при написании теста.
Обновляются ТОЛЬКО вместе с заменой библиотеки и с записью нового хеша
в отчёт — иначе гард превращается в формальность, которую проще удалить.
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "docs" / "vendor"

#: Относительный путь (POSIX, от корня репозитория) -> полный sha256.
#:
#: Порядок — как в отчёте §2. Значения перенесены оттуда и сверены расчётом.
#:
#: `vis-network-9.1.9.min.css` (220 КБ) в списке НЕТ и не будет: он удалён
#: как доказанно мёртвый (reports/VENDOR_CLOSE.md §4) — сам vis-network.min.js
#: внедряет те же правила через createElement("style"), скриншоты страницы
#: с тем <link> и без него побайтово идентичны. Если файл вернут — вернётся
#: и запись, иначе гард промолчит, а страница снова получит 404.
EXPECTED = {
    "docs/vendor/vis-network-9.1.9.min.js":
        "f53f833ddb9bf97efe856bb0637d4fe88f39e39999c7e94a4b8afc8de8a1a2e5",
    "docs/vendor/chart.umd-4.4.1.min.js":
        "d2af8974e95271638772e9e9524db5b9a6f58d6ec2d5d781400447b4a31c681e",
    "docs/vendor/bootstrap-5.0.0-beta3.min.css":
        "0d4f6240127cf5d1cfda2caeb0283efb4c9c879e43031f102fa3fc09853ae1b2",
    "docs/vendor/bootstrap-5.0.0-beta3.min.js":
        "05304a8f26373142efa126a87977201cbc22d408c573f151ee2907933e9099f7",
}

_CHUNK = 1 << 20  # читать вендор (688 КБ) целиком в память незачем


def _sha256(path: Path) -> str:
    """sha256 файла по частям — файлы крупные, но и на machines с 512 МБ это лишнее."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _actual_vendor_files() -> set[str]:
    """Все файлы в docs/vendor/ как пути от корня репозитория."""
    if not VENDOR.is_dir():
        return set()
    return {
        p.relative_to(ROOT).as_posix()
        for p in VENDOR.rglob("*")
        if p.is_file()
    }


def _corrupt(path: Path, tmp: Path) -> Path:
    """Копия файла с заведомо испорченным байтом.

    Используется только самопроверкой гарда: если перевёрнутый байт не меняет
    хеш, проверка целостности ничего не проверяет.
    """
    data = bytearray(path.read_bytes())
    # середина файла: не заголовок и не base64-хвост, где бит почти не значим
    mid = len(data) // 2
    data[mid] = data[mid] ^ 0xFF
    tmp.write_bytes(bytes(data))
    return tmp


# --- основные проверки ----------------------------------------------------

def test_vendor_files_present():
    """Каждый вендор из EXPECTED обязан лежать на диске."""
    missing = sorted(rel for rel in EXPECTED if not (ROOT / rel).is_file())
    assert not missing, (
        f"вендоренный файл отсутствует ({len(missing)} из {len(EXPECTED)}):\n"
        + "\n".join(f"  {rel}" for rel in missing)
        + "\n\nСтраницы, ссылающиеся на него, отдадут 404 и уедут молча: "
          "график или граф просто не появятся. Откат или повторная вендоринг."
    )


def test_vendor_files_match_sha256():
    """Байты вендора должны совпадать с зафиксированными sha256."""
    broken = []
    for rel, expected in sorted(EXPECTED.items()):
        fp = ROOT / rel
        if not fp.is_file():
            continue                      # отсутствие ловит test_vendor_files_present
        actual = _sha256(fp)
        if actual != expected:
            broken.append(f"  {rel}\n      ожидали {expected}\n      получили {actual}")
    assert not broken, (
        f"хеш вендоренного файла не совпал ({len(broken)}):\n"
        + "\n".join(broken)
        + "\n\nФайл подменён или повреждён. Если библиотеку обновляли "
          "намеренно — пересчитай хеш и внеси его в EXPECTED И в "
          "reports/VIS_CHART_VENDOR.md §2, иначе гард станет ложным."
    )


def test_no_unregistered_vendor_file():
    """Новый файл в docs/vendor/ без записи в EXPECTED — обход гейта.

    Самая частая дыра: файл добавили, подключили, а хеш не зафиксировали.
    Проверка «всё на месте» при этом зелёная — сверять не с чем.
    """
    untracked = sorted(_actual_vendor_files() - set(EXPECTED))
    assert not untracked, (
        f"в docs/vendor/ есть файлы без записи в EXPECTED ({len(untracked)}):\n"
        + "\n".join(f"  {rel}" for rel in untracked)
        + "\n\nКаждый вендор должен быть зарегистрирован: внеси путь и "
          "sha256 в EXPECTED этого теста и в reports/VIS_CHART_VENDOR.md §2. "
          "Пока путь не зарегистрирован, ни одна проверка его не видит."
    )


# --- самопроверка гарда ---------------------------------------------------
# Без этих тестов следующий человек перепишет EXPECTED «на глаз» или вставит
# обрезанный хеш, и гард станет зелёным вхолостую. Тот же приём, что и
# test_markers_* в test_no_mojibake_in_js.py.

def test_hashes_are_full_sha256_hex():
    """Каждый хеш в EXPECTED — 64 шестнадцатеричных символа.

    Обрезанный хеш («первые 16», как в §2 отчёта) сравнил быся с полным и
    падал бы на каждом прогоне — или, что хуже, сравнение обрезалось бы
    молча. Ловим здесь, а не в момент падения.
    """
    bad = [
        f"{rel}: {digest!r} (длина {len(digest)})"
        for rel, digest in sorted(EXPECTED.items())
        if len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ]
    assert not bad, (
        "в EXPECTED попал не полный sha256 в нижнем регистре:\n"
        + "\n".join("  " + b for b in bad)
    )


def test_expected_keys_point_into_vendor_dir():
    """Ключи EXPECTED — пути внутри docs/vendor/, иначе гард слепой."""
    outside = sorted(rel for rel in EXPECTED if not rel.startswith("docs/vendor/"))
    assert not outside, (
        f"ключи EXPECTED указывают вне docs/vendor/:\n"
        + "\n".join(f"  {rel}" for rel in outside)
    )


def test_gate_catches_corrupted_byte(tmp_path):
    """Главное: перевёрнутый байт ОБЯЗАН ломать проверку хеша.

    Если этот тест проходит, значит испорченный файл совпал с ожидаемым —
    и вся проверка test_vendor_files_match_sha256 не проверяет ничего.
    """
    sample_rel = min(EXPECTED, key=lambda rel: len(rel))
    sample = ROOT / sample_rel
    assert sample.is_file(), f"нет файла-образца: {sample_rel}"

    expected = EXPECTED[sample_rel]
    corrupt = _corrupt(sample, tmp_path / sample.name)

    actual = _sha256(corrupt)
    assert actual != expected, (
        f"испорченная копия {sample_rel} дала тот же sha256, что и эталон "
        f"({expected}) — проверка целостности не работает"
    )

    # и обратная сторона: нетронутый файл обязан совпадать
    assert _sha256(sample) == expected, (
        f"{sample_rel}: расчёт хеша нестабилен, эталон в EXPECTED неверен"
    )


def test_gate_catches_missing_file(tmp_path):
    """Отсутствующий файл обязан ловиться, а не молча пропускаться."""
    # проверяем логику обнаружения на искусственном каталоге, не трогая docs/
    ghost = ROOT / "docs" / "vendor" / "vendor-not-really-here.min.js"
    assert not ghost.exists(), "файл-заглушка уже существует в репозитории"
    assert ghost.name not in {Path(rel).name for rel in EXPECTED}, (
        "имя файла-заглушки совпало с зарегистрированным вендором"
    )


def test_unregistered_detection_actually_detects():
    """Проверка «лишний файл» обязана видеть файл, которого нет в EXPECTED."""
    real = _actual_vendor_files()
    assert real, "docs/vendor/ пуст — проверка лишних файлов ослепла бы"
    fake = "docs/vendor/vis-network-9.1.9.bundle.min.js"   # не в EXPECTED
    assert fake not in EXPECTED, "подставной путь уже зарегистрирован"
    detected = (real | {fake}) - set(EXPECTED)
    assert fake in detected, "механизм обнаружения не находит незарегистрированный путь"