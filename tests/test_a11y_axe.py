"""
WCAG 2.2 через axe-core — гейт доступности, собранный на том же браузерном
конвейере, что и визуальные снапшоты.

Зачем
-----
vortix-cli отдавал по доступности 43 ошибки, но 294 из 338 его ошибок вообще
были ложными (баг `bugs.broken-links`, см. reports/SKILLS_INSTALL.md §4.1),
и это делает его источником правды непригодным. axe-core — отдельный,
закоммиченный движок проверки: его версия зафиксирована в репозитории
(tests/vendor/axe.min.js), и результат воспроизводится офлайн, без сети и без
чужого npm-пакета, который может обновиться и поменять вывод.

Что меряется (замерено, а не предположено)
------------------------------------------
Прогон 18 страниц x 2 разрешения против axe-core 4.13.0 с тегами
wcag2a / wcag2aa / wcag2aaa / wcag21a / wcag21aa / wcag22aa:

    critical          0 узлов
    serious        1264 узла, три правила:
      color-contrast-enhanced    1218   (AAA, 7:1)
      color-contrast               41   (AA, 4.5:1)
      scrollable-region-focusable    5   (AA)

Два вывода, которые определили конструкцию гейта:

1. **Критичных нарушений нет ни одного.** Гейт «падает только на critical»,
   как его сформулировали, был бы зелёным всегда и не защищал бы ничего:
    1264 серьёзных нарушения прошли бы молча. Поэтому critical — жёсткий
    запрет без исключений, а serious — гейт с базовой линией.

2. **1218 из 1264 узлов — это AAA (7:1).** Требовать 7:1 как условие прохождения
   теста неразумно: ни один обычный сайт этого не выполняет, и гейт
   превратился бы в вечный красный шум, который отключат на второй день.
    Поэтому правила, у которых ТОЛЬКО теги AAA, сканируются и попадают в
    отчёт, но не валят прогон; валят всё, что относится к A/AA.

Как проверяется
---------------
    0 critical — всегда падение, базовая линия не может это оправдать;
    правила A/AA — падение, если правило новое или узлов стало больше
                    базового числа (регрессия);
    правила AAA   — пишутся в отчёт, в вердикт не входят;
    исчезнувшие правила — сообщаются как «исправлено», падением не являются.

Числа узлов сняты один раз и лежат в tests/a11y_baseline.json. Переснимать
базу можно только осознанно:

    $env:UPDATE_A11Y_BASELINE="1"; RUN_A11Y=1 pytest -q -m a11y

Как запускать
-------------
    python -m http.server 8000 --directory docs     # из корня репозитория
    $env:RUN_A11Y="1"; pytest -q -m a11y             # только доступность
    $env:RUN_SNAPSHOTS="1"; pytest -q -m snapshots   # только снапшоты

Гейт на переменной окружения, а не на `-m` в addopts: `-m` из командной строки
ПЕРЕКРЫВАЕТ addopts (измерено в tests/conftest.py, см. докстринг там).
Обычный `pytest -q` эти тесты не собирает — им нужен браузер и запущенный
сервер, а полный прогон должен оставаться быстрым (~4 с).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

# Матрица страниц и разрешений, константы темы и таймаутов берутся из
# тестового модуля снапшотов, а не дублируются. Дублирование здесь означало бы
# две правки при добавлении страницы и тихо разошёдшиеся наборы: снимок снят,
# а доступность не проверялась (или наоборот).
# Импорт через пакет `tests.`, потому что в tests/ есть __init__.py.
from tests.test_visual_snapshots import (  # noqa: E402  (после importorskip)
    BASE_URL,
    COLOR_SCHEME,
    NAV_TIMEOUT_MS,
    PAGES,
    SETTLE_MS,
    VIEWPORTS,
    _check_server,
    _slug,
)

ROOT = Path(__file__).resolve().parents[1]
AXE_PATH = Path(__file__).resolve().parent / "vendor" / "axe.min.js"
BASELINE_PATH = Path(__file__).resolve().parent / "a11y_baseline.json"
REPORT_DIR = Path(__file__).resolve().parent / "a11y_report"

UPDATE_BASELINE = os.environ.get("UPDATE_A11Y_BASELINE") == "1"

#: axe-core 4.13.0. Версия зафиксирована файлом в репозитории, поэтому этот
#: тест не зависит ни от сети, ни от того, что npm-пакет обновится.
AXE_VERSION = "4.13.0"

#: WCAG 2.2, уровни A + AA + AAA. Тега `wcag22aaa` в axe-core нет — AAA
#: автоматизируется частично, и набор правил axe на этом уровне ограничен.
#: Он перечислен явно, чтобы отсутствие было видно, а не молчаливым.
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag22aa"]

#: Теги, которые делают правило «гейтовым». Правило с ТОЛЬКО тегами из этого
#: списка попадает в отчёт, но не валит прогон (см. докстринг, п.2).
GATE_TAGS = {"wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"}

#: Влияние, которое невозможно оправдать базовой линией ни при каких условиях.
NEVER_ALLOWED = {"critical"}

KILL_CSS = ("*,*::before,*::after{transition:none!important;"
            "animation:none!important;caret-color:transparent!important}")

RUN_AXE = """
async (tags) => await axe.run(document, {
    runOnly: {type: 'tag', values: tags},
    resultTypes: ['violations'],
})
"""

# Только `a11y`. Маркер `snapshots` намеренно НЕ ставится: это отдельный
# гейт с отдельной командой, и смешивание маркеров однажды уже стоило прогона
# (замерено в tests/conftest.py: фильтр по `snapshots` отбрасывал и a11y-тесты,
# `RUN_A11Y=1 pytest -m a11y` давал 0 selected).
pytestmark = [pytest.mark.a11y]

playwright_api = pytest.importorskip("playwright.sync_api",
                                     reason="playwright не установлен")


# ─────────────────────────── окружение ───────────────────────────

@pytest.fixture(scope="session")
def axe_source() -> str:
    if not AXE_PATH.exists():
        pytest.skip(f"нет {AXE_PATH} — vendored axe-core не найден")
    return AXE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def browser():
    with playwright_api.sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001 — причина уедет в текст skip
            pytest.skip(f"Chromium не запускается: {exc}. "
                        f"Поставь: playwright install chromium")
        yield b
        b.close()


@pytest.fixture(scope="session")
def _env_checked(browser):  # noqa: ARG001 — фикстура только ради порядка
    _check_server()
    return True


def _baseline() -> dict:
    if not BASELINE_PATH.exists():
        return {}
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


# ─────────────────────────── прогон axe ───────────────────────────

def _run_axe(page, axe_js: str, url: str) -> list[dict]:
    """Зайти на страницу, дождаться отрисовки, прогнать axe-core."""
    page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
    # Контраст считается по фактически применённым цветам, поэтому анимации
    # гасим и ждём шрифт — иначе замер может сойтись на полурисованном тексте.
    page.add_style_tag(content=KILL_CSS)
    page.evaluate("() => document.fonts.ready")
    page.wait_for_timeout(SETTLE_MS)
    page.add_script_tag(content=axe_js)

    raw = page.evaluate(RUN_AXE, WCAG_TAGS)
    out = []
    for v in raw["violations"]:
        wcag = [t for t in v.get("tags", []) if t.startswith("wcag")]
        out.append({
            "id": v["id"],
            "impact": v.get("impact"),
            "help": v.get("help"),
            "nodes": len(v["nodes"]),
            "wcag_tags": wcag,
            "gated": bool(set(wcag) & GATE_TAGS),
            "targets": [n["target"][0] if n["target"] else "?"
                        for n in v["nodes"][:5]],
        })
    return sorted(out, key=lambda x: (x["id"] or ""))


def _fmt(v: dict, allowed: int | None) -> str:
    head = f"  {v['id']} [{v['impact']}] — {v['nodes']} узлов"
    if not v["gated"]:
        head += "  (AAA, в вердикт не входит)"
    elif allowed is not None:
        head += f" (база {allowed}, рост +{v['nodes'] - allowed})"
    return (f"{head}\n      {v['help']}\n"
            f"      {', '.join(v['targets'])}")


def _verify(name: str, violations: list[dict]) -> None:
    """Сравнить с базой. Падение = critical, новое правило или рост узлов."""
    base_all = _baseline()

    # ── ветка пересъёмки базы ────────────────────────────────────────────────
    # Возврат стоит ДО расчёта нарушений. В этом режиме проверки нет — есть
    # запись новых чисел, поэтому считать fatal/gone/aaa после return было бы
    # вычислением в никуда: три прохода по списку ради результата, который
    # здесь не используется.
    if UPDATE_BASELINE:
        base_all[name] = {v["id"]: v["nodes"]
                          for v in violations if v["gated"]}
        BASELINE_PATH.write_text(
            json.dumps(base_all, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        return

    # ── ветка проверки ──────────────────────────────────────────────────────
    base = base_all.get(name, {})

    fatal: list[str] = []
    for v in violations:
        if v["impact"] in NEVER_ALLOWED:
            fatal.append(_fmt(v, None))
            continue
        if not v["gated"]:
            continue                      # AAA — в отчёт, но не в вердикт
        prev = base.get(v["id"])
        if prev is None:
            fatal.append(_fmt(v, None) + "\n      Правила не было в базе — "
                                             "новое нарушение A/AA.")
        elif v["nodes"] > prev:
            fatal.append(_fmt(v, prev) + "\n      Узлов стало больше, чем в базе.")

    if not fatal:
        return

    # Обратное направление сообщаем, но не валим: исчезновение нарушения —
    # улучшение, и требовать его базой бессмысленно.
    now = {v["id"] for v in violations}
    gone = sorted(k for k in base if k not in now)
    aaa = [v for v in violations if not v["gated"]]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    report = REPORT_DIR / f"{name}.json"
    report.write_text(json.dumps(violations, ensure_ascii=False, indent=1),
                      encoding="utf-8")

    extra = ""
    if aaa:
        tot = sum(v["nodes"] for v in aaa)
        extra += (f"\n  AAA-нарушения (не в вердикте, {tot} узлов): "
                  + ", ".join(f"{v['id']}×{v['nodes']}" for v in aaa))
    if gone:
        extra += f"\n  Исправлено с прошлой базы: {', '.join(gone)}"

    pytest.fail(f"{name}: нарушений A/AA, которые не оправданы базой — "
                f"{len(fatal)}\n" + "\n".join(fatal) + extra +
                f"\n    полный отчёт: {report}\n"
                f"    Базу переснимают только осознанно:\n"
                f"    $env:UPDATE_A11Y_BASELINE='1'; RUN_A11Y=1 pytest -q -m a11y")


# ─────────────────────────── тесты ───────────────────────────

@pytest.mark.parametrize("page_name", PAGES)
@pytest.mark.parametrize("width,height", VIEWPORTS, ids=lambda v: str(v))
def test_a11y_wcag22(_env_checked, browser, axe_source, page_name, width, height):
    """WCAG 2.2 A/AA: критичных нарушений нет, регрессий против базы нет."""
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        service_workers="block",
        reduced_motion="reduce",
        color_scheme=COLOR_SCHEME,
    )
    page = ctx.new_page()
    try:
        violations = _run_axe(page, axe_source,
                              f"{BASE_URL}/{page_name}.html")
    finally:
        ctx.close()
    _verify(f"{_slug(page_name)}-{width}", violations)


def test_a11y_baseline_is_present(_env_checked):  # noqa: ARG001
    """Файл базы обязан существовать и читаться: без него гейт молчит.

    Отдельный тест, потому что состояние «базы нет» — это ровно то, при котором
    `_verify` не упала бы ни на одном правиле: проверять нечего, и всё
    молча проходит. Непустоты записей здесь НЕ требуется: запись `{}` означает
    «нарушений A/AA нет» и проверяется наравне с остальными.
    """
    if UPDATE_BASELINE:
        pytest.skip("переснимается база")
    base = _baseline()
    assert base, (
        f"{BASELINE_PATH.name} пуст или отсутствует — гейт доступности не имеет "
        f"базы и пропустит всё. Сними её целиком, БЕЗ -k:\n"
        f"    $env:UPDATE_A11Y_BASELINE='1'; RUN_A11Y=1 pytest -q -m a11y"
    )


def test_a11y_baseline_covers_every_page(_env_checked):  # noqa: ARG001
    """База обязана покрывать всю матрицу, иначе гейт слепнет.

    Проверяется ПОКРЫТИЕ, а не непустота: запись `{}` — не поломка, а честный
    результат «на этой странице нарушений A/AA нет», и гейт продолжает её
    контролировать (любое новое нарушение станет «новым правилом» и уронит
    прогон). Опасен именно неполный файл базы.

    Отдельный тест, потому что при неполной базе `_verify` не упала бы ни на
    одном правиле: у страницы без записи любое нарушение трактуется как
    «новое», то есть проверка молча превращается в «здесь ничего не
    проверяем». Именно это и получается, если снимать базу с фильтром:
    замерено, `-k "index and 1280"` создал базу из одной записи из 36.
    """
    if UPDATE_BASELINE:
        pytest.skip("переснимается база")
    base = _baseline()

    expected = {f"{_slug(p)}-{w}" for p in PAGES for w, _ in VIEWPORTS}
    missing = sorted(expected - set(base))
    assert not missing, (
        f"в базе нет {len(missing)} из {len(expected)} комбинаций "
        f"страница/разрешение: {', '.join(missing)}\n"
        f"    Эти страницы гейт не контролирует. Пересними базу целиком, БЕЗ -k:\n"
        f"    $env:UPDATE_A11Y_BASELINE='1'; RUN_A11Y=1 pytest -q -m a11y"
    )

    # Записи вне матрицы: страница переименована или удалена, а база о ней помнит.
    # Молчаливое расхождение — источник будущих ложных падений.
    stale = sorted(set(base) - expected)
    assert not stale, (
        f"в базе {len(stale)} записей, которых нет в PAGES x VIEWPORTS: "
        f"{', '.join(stale)}\n"
        f"    Похоже на переименованную или удалённую страницу. Пересними базу."
    )


def test_a11y_axe_version_pinned():
    """Версия axe-core зафиксирована в репозитории и совпадает с ожидаемой.

    Без этого теста тихая смена вендоренного файла изменила бы и вердикт, и
    число узлов в базе — и расхождение выглядело бы как поломка вёрстки.
    """
    src = AXE_PATH.read_text(encoding="utf-8")
    m = re.search(r"axe\.version\s*=\s*['\"]([\d.]+)['\"]", src)
    assert m, f"в {AXE_PATH.name} не найден axe.version — файл подменён?"
    found = m.group(1)
    assert found == AXE_VERSION, (
        f"в tests/vendor/axe.min.js версия {found}, а тест ждёт {AXE_VERSION}. "
        f"Либо верни файл, либо обнови AXE_VERSION и пересними базу: "
        f"$env:UPDATE_A11Y_BASELINE='1'; RUN_A11Y=1 pytest -q -m a11y"
    )
