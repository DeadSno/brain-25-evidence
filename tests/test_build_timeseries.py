"""QA-P1-04: tests/test_build_timeseries.py

`scripts/build_timeseries.py` собирает `data/timeseries/{pubmed,wiki,citations}.json`
в `docs/timeseries.json` — единственный источник кривых для `docs/trends.html`.
Страница грузит файл одним `fetch` (trends.html:1078) и при ошибке логирует
предупреждение, продолжая рендер с пустыми данными (trends.html:1082-1085).
То есть отказ генератора виден только в консоли, а тихая порча — нет:

  * нет ключа `pubmed` → `TS.pubmed || {}` даёт `{}` (trends.html:496,525,574),
    все три блока графиков рисуются пустыми без единой ошибки;
  * нет ключа `citations` → суммы KPI по цитированиям (trends.html:516-517)
    и scatter считаются от нуля, страница показывает «+0 %»;
  * нестроковый ключ года (`"20-15"`, `2015` как число) → `c['2015'] || 0`
    молча даёт 0, то есть потерянный год неотличим от года без публикаций;
  * нечисловое значение (`"н/д"`, `null`) → в арифметике `NaN`, и KPI
    превращаются в `NaN` прямо в тексте страницы.

Всё это проверяется ниже на фикстуре из трёх карточек и на закоммиченном
файле. Точное количество ключей и конкретные id НЕ проверяются, кроме
покрытия: покрытие pubmed/citations = 100 % карточек — это инвариант,
восстановленный в DATA-P1-12 (было 94/130), и именно он ловит возврат
дефекта. У wiki покрытие 90/130 и это by design (25 карточек без статьи
ru.wikipedia), поэтому у него нижняя граница, а не равенство.

Сеть не используется. Живой репозиторий тесты не трогают: генератор всегда
запускается на копии в tmp_path.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_timeseries.py"
COMMITTED = ROOT / "docs" / "timeseries.json"
SRC_DIR = ROOT / "data" / "timeseries"
PAGE = ROOT / "docs" / "trends.html"
INDEX = ROOT / "docs" / "data_index.json"

#: Источники рядов. Порядок берётся из SOURCES в build_timeseries.py:10 и
#: попадает в артефакт как _meta.sources. test_sources_match_page следит,
#: чтобы список в тесте, в генераторе и на странице не разошлись.
SOURCES = ("pubmed", "wiki", "citations")

#: Ключ года у разных источников разный: у pubmed/citations — «2025»,
#: у wiki — помесячные «2025-06». Числовые ключи без строк приводят к
#: молчаливому нулю в c['2015'] || 0 (trends.html:517).
YEAR_RE = re.compile(r"^\d{4}(?:-\d{2})?$")

#: Минимум ключей в источнике закоммиченного файла. Реально 130/90/130;
#: 1 — слишком мягко (потерять 128 карточек и остаться «зелёным»).
MIN_KEYS = {"pubmed": 100, "wiki": 50, "citations": 100}

#: Нижняя граница покрытия wiki. Полное равенство здесь неприменимо:
#: 40 карточек не имеют статьи ru.wikipedia, и добирать их нечем.
#: Факт на 14.10.2026 — 90 из 130 (69 %); граница ниже с запасом,
#: чтобы ловить потерю половины рядов, а не спор о двух карточках.
WIKI_COVERAGE_FLOOR = 0.6

#: Файл меньше этого — заглушка. Реальный ~196 КБ.
MIN_BYTES = 1024


# ── Фикстура входа ───────────────────────────────────────────────────────────
#
# Три карточки: у одной полный набор рядов, у одной только citations,
# у одной — wiki с помесячными ключами. Плюс два края: пустой ряд
# (нули — не отсутствие) и ряд с пропуском года.

ROWS = {
    "pubmed": {
        "ААА": {"2015": 10, "2020": 20, "2025": 30},
        "БББ": {"2015": 1, "2016": 0, "2017": 5},
        "ВВВ": {"2025": 0},
    },
    "wiki": {
        "ААА": {"2020-01": 100, "2020-02": 150, "2025-06": 200},
        "ВВВ": {"2025-01": 7},
    },
    "citations": {
        "ААА": {"2015": 3, "2025": 40},
        "БББ": {"2015": 0, "2025": 0},
    },
}


def _env(console: str = "utf-8") -> dict:
    env = dict(os.environ)
    # Иначе дочерний Python на Windows возьмёт кодировку консоли (cp1251/cp866)
    # и русские сообщения генератора превратятся в «кракозябры».
    env["PYTHONIOENCODING"] = console
    return env


def make_repo(tmp_path: Path, rows: dict[str, dict] | None = None) -> Path:
    """Репозиторий с data/timeseries/*.json и копией генератора.

    Генератор берёт пути от __file__ (parents[1]), поэтому layout повторяет
    живой: scripts/ рядом с data/ и docs/ (docs/ создаёт он сам).
    """
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "data" / "timeseries").mkdir(parents=True)
    for source, payload in (ROWS if rows is None else rows).items():
        (root / "data" / "timeseries" / f"{source}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    shutil.copy(SCRIPT, root / "scripts" / SCRIPT.name)
    return root


def run_generator(root: Path, console: str = "utf-8") -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / SCRIPT.name)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_env(console),
    )
    return proc.returncode, proc.stdout + proc.stderr


def load_series(root: Path) -> dict:
    out = root / "docs" / "timeseries.json"
    assert out.is_file(), "генератор не создал docs/timeseries.json"
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.fixture()
def built(tmp_path):
    """Ряды, собранные из ROWS. Запуск падает здесь же, если rc != 0."""
    root = make_repo(tmp_path)
    rc, out = run_generator(root)
    assert rc == 0, f"генератор упал:\n{out}"
    return load_series(root)


@pytest.fixture(scope="module")
def committed() -> dict:
    assert COMMITTED.is_file(), f"нет {COMMITTED.name} — графики на trends не отрисуются"
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


# ── Генератор на фикстуре ────────────────────────────────────────────────────


def test_generator_runs_without_errors(tmp_path):
    """Главный сценарий QA-P1-04: генератор обязан отработать и создать файл."""
    root = make_repo(tmp_path)
    rc, out = run_generator(root)
    assert rc == 0, out
    assert (root / "docs" / "timeseries.json").is_file(), out
    assert "[OK]" in out, f"генератор не отчитался об успехе:\n{out}"


def test_meta_lists_sources(built):
    """_meta.sources — единственное место, где страница может узнать состав."""
    assert built["_meta"]["sources"] == list(SOURCES), (
        f"_meta.sources = {built['_meta'].get('sources')}, ожидалось {list(SOURCES)}"
    )


def test_only_meta_and_known_sources(built):
    """Лишний верхнеуровневый ключ страница не прочитает — но и не сломается.

    Проверяем обратное: `_meta` и три источника обязаны БЫТЬ, а состав
    сверяется с SOURCES, чтобы источник не исчез молча.
    """
    assert "_meta" in built, f"в файле нет _meta: {sorted(built)}"
    for source in SOURCES:
        assert source in built, f"в файле нет источника {source!r}: {sorted(built)}"


def test_each_source_is_dict_of_dicts(built):
    """Ряд — dict[id -> dict[год -> число]]. Иначе Object.entries даёт мусор."""
    for source in SOURCES:
        part = built[source]
        assert isinstance(part, dict), f"{source}: не объект, а {type(part).__name__}"
        assert part, f"{source}: 0 карточек — график пустой"
        for name, series in part.items():
            assert isinstance(series, dict), (
                f"{source}[{name!r}]: не объект, а {type(series).__name__}"
            )


def test_year_keys_are_wellformed(built):
    """Ключ года — строка вида «2025» или «2025-06».

    Числовой ключ даёт c['2015'] → undefined → 0, и потерянный год
    становится неотличим от года без публикаций (trends.html:517).
    """
    for source in SOURCES:
        for name, series in built[source].items():
            for key in series:
                assert isinstance(key, str), (
                    f"{source}[{name!r}]: ключ {key!r} не строка — "
                    f"сравнение по году вернёт 0 молча"
                )
                assert YEAR_RE.match(key), (
                    f"{source}[{name!r}]: ключ {key!r} не похож на год "
                    f"(ожидается «2025» или «2025-06»)"
                )


def test_values_are_nonnegative_numbers(built):
    """Значение — число ≥ 0. null/строка дают NaN в KPI и текст «NaN %»."""
    for source in SOURCES:
        for name, series in built[source].items():
            for key, value in series.items():
                assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                    f"{source}[{name!r}][{key!r}]: {value!r} не число — "
                    f"арифметика даст NaN на странице"
                )
                assert value >= 0, f"{source}[{name!r}][{key!r}]: отрицательное {value}"


def test_merges_every_source_file(tmp_path):
    """Каждый из трёх файлов попадает в результат — потеря источника не тихая."""
    root = make_repo(tmp_path)
    rc, out = run_generator(root)
    assert rc == 0, out
    built = load_series(root)
    for source in SOURCES:
        src = json.loads(
            (root / "data" / "timeseries" / f"{source}.json").read_text(encoding="utf-8")
        )
        assert built[source] == src, (
            f"{source}: содержимое не совпало с исходным файлом — "
            f"генератор что-то переписал по дороге"
        )


def test_missing_source_file_is_skipped(tmp_path):
    """Отсутствующий data/timeseries/*.json → [SKIP], а не исключение.

    Иначе на машине без wiki.json нельзя было бы пересобрать ни pubmed,
    ни citations: файл лежит в git, но локально может быть не выкачан.
    """
    rows = {k: v for k, v in ROWS.items() if k != "wiki"}
    root = make_repo(tmp_path, rows)
    rc, out = run_generator(root)
    assert rc == 0, out
    assert "[SKIP]" in out, f"генератор не сообщил о пропуске wiki:\n{out}"
    built = load_series(root)
    assert "wiki" not in built, "пропущенный источник попал в артефакт"
    assert built["_meta"]["sources"] == list(SOURCES), (
        "SOURCES в _meta перечисляет источник, которого в файле нет — "
        "страница получит undefined вместо {}"
    )


def test_all_sources_missing_still_valid(tmp_path):
    """Пустой data/timeseries/ обязан дать валидный файл с _meta, а не падать."""
    root = make_repo(tmp_path, {})
    rc, out = run_generator(root)
    assert rc == 0, out
    built = load_series(root)
    assert built["_meta"]["sources"] == list(SOURCES)
    assert set(built) == {"_meta"}, f"в файле лишние ключи: {sorted(built)}"


def test_broken_source_file_fails_loudly(tmp_path):
    """Битый вход обязан валить генератор, а не молча выдавать пустой файл.

    json.loads без обработки → ненулевой код возврата, хук pre-commit
    прерывает коммит. Тихая пустота здесь означала бы, что страница
    потеряла все кривые без единого сообщения.
    """
    root = make_repo(tmp_path)
    (root / "data" / "timeseries" / "pubmed.json").write_text("{oops", encoding="utf-8")
    rc, _ = run_generator(root)
    assert rc != 0, "битый data/timeseries/pubmed.json не остановил генератор"


def test_generator_is_deterministic(tmp_path):
    """Две сборки из одного входа — байт в байт.

    json.dumps без sort_keys даёт порядок ключей исходного файла, но он
    одинаков при двух прогонах по одному и тому же входу. Расхождение
    означало бы нестабильность, и артефакт мерцал бы сам собой.
    """
    root = make_repo(tmp_path)
    rc, _ = run_generator(root)
    assert rc == 0
    first = (root / "docs" / "timeseries.json").read_bytes()
    rc, out = run_generator(root)
    assert rc == 0, out
    second = (root / "docs" / "timeseries.json").read_bytes()
    assert first == second, "две сборки из одних data/timeseries/*.json разошлись"


def test_runs_under_legacy_console_encoding(tmp_path):
    """Под cp1251 русские сообщения превращаются в «кракозябры», но rc == 0.

    Проверяем, что вывод не влияет на результат и код возврата: иначе
    pre-commit на Windows-консоли ронял бы коммиты из-за кодировки.
    """
    root = make_repo(tmp_path)
    rc, _ = run_generator(root, console="cp1251")
    assert rc == 0, "генератор упал под cp1251"
    assert (root / "docs" / "timeseries.json").is_file()


# ── Закоммиченный артефакт: то, что реально грузит страница ─────────────────


@pytest.mark.parametrize("source", SOURCES)
def test_committed_source_present(committed, source):
    """Ключ источника обязан существовать — иначе `TS.pubmed || {}` даёт {}."""
    assert source in committed, (
        f"в {COMMITTED.name} нет {source!r}: {sorted(committed)} — "
        f"графики этого источника не отрисуются без ошибки"
    )


@pytest.mark.parametrize("source", SOURCES)
def test_committed_source_not_empty(committed, source):
    part = committed[source]
    assert isinstance(part, dict), f"{source}: не объект, а {type(part).__name__}"
    assert len(part) >= MIN_KEYS[source], (
        f"{source}: {len(part)} карточек, ожидалось не меньше {MIN_KEYS[source]} — "
        f"ряд почти пуст, страница покажет пустой график"
    )


@pytest.mark.parametrize("source", SOURCES)
def test_committed_series_shape(committed, source):
    """Форма серий на живом файле: id -> str-год -> число ≥ 0."""
    for name, series in committed[source].items():
        assert isinstance(name, str) and name, f"{source}: нестроковый или пустой id"
        assert isinstance(series, dict) and series, (
            f"{source}[{name!r}]: пустая серия — кривой не из чего построить"
        )
        for key, value in series.items():
            assert isinstance(key, str) and YEAR_RE.match(key), (
                f"{source}[{name!r}]: ключ {key!r} не строка-год"
            )
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                f"{source}[{name!r}][{key!r}]: {value!r} не число"
            )
            assert value >= 0, f"{source}[{name!r}][{key!r}]: отрицательное {value}"


@pytest.mark.parametrize("source", ("pubmed", "citations"))
def test_committed_covers_every_card(committed, source):
    """Покрытие pubmed/citations = 100 % карточек.

    Это инвариант DATA-P1-12: до него было 94/130, и страница обещала 130
    кривых, рисуя 94. 36 недостающих ключей нашлись в data_pubmed_terms.json,
    серии добрали fetch_timeseries.py. Возврат дефекта должен краснеть здесь.

    Новая карточка без серий тоже даст красный — и это правильно: сначала
    fetch_timeseries.py, потом коммит.
    """
    ids = _index_ids()
    missing = sorted(ids - set(committed[source]))
    assert not missing, (
        f"{source}: {len(missing)} карточек без серий из {len(ids)}, "
        f"например {missing[:5]}. Добрать: fetch_timeseries.py --source {source}"
    )


def test_committed_wiki_coverage_floor(committed):
    """У wiki полное покрытие не требуется: часть карточек без статьи ru.wikipedia.

    Нижняя граница вместо равенства: 90/130 — норма, падать должна только
    на настоящей потере (пустой файл, половина ключей пропала).
    """
    ids = _index_ids()
    share = len(set(committed["wiki"]) & ids) / len(ids)
    assert share >= WIKI_COVERAGE_FLOOR, (
        f"wiki покрывает {share:.0%} карточек, ожидалось не меньше "
        f"{WIKI_COVERAGE_FLOOR:.0%} (в норме 90/130)"
    )


@pytest.mark.parametrize("source", SOURCES)
def test_committed_keys_are_known_cards(committed, source):
    """Ключ серии обязан соответствовать карточке из data_index.json.

    Страница ищет ряд по id карточки (trends.html:753-755, 870), и лишний
    ключ не рисуется, а потерянный — молча: кривой просто нет.
    """
    ids = _index_ids()
    unknown = sorted(set(committed[source]) - ids)
    assert not unknown, (
        f"{source}: {len(unknown)} ключей не соответствуют ни одной карточке, "
        f"например {unknown[:5]}"
    )


def test_committed_file_not_truncated():
    """196 КБ → файл должен быть больше 1 КБ: заглушка прошла бы форму, но не размер."""
    size = COMMITTED.stat().st_size
    assert size > MIN_BYTES, f"{COMMITTED.name} — {size} Б, это не ряды"


def test_sources_match_generator():
    """SOURCES теста == SOURCES генератора.

    Страница обращается к TS.pubmed / TS.wiki / TS.citations поимённо
    (trends.html:496,509,516). Источник, переименованный в генераторе,
    даст пустой блок графиков без ошибки — расхождение обязано краснеть.
    """
    src = SCRIPT.read_text(encoding="utf-8")
    m = re.search(r"^SOURCES\s*=\s*\[([^\]]*)\]", src, re.MULTILINE)
    assert m, "в build_timeseries.py нет SOURCES"
    script_sources = [s.strip().strip("\"'") for s in m.group(1).split(",") if s.strip()]
    assert script_sources == list(SOURCES), (
        f"генератор собирает {script_sources}, тест ждёт {list(SOURCES)}"
    )


def test_sources_match_page():
    """Каждый источник из SOURCES читается страницей как TS.<source>."""
    html = PAGE.read_text(encoding="utf-8")
    for source in SOURCES:
        assert f"TS.{source}" in html or f"TS_.{source}" in html, (
            f"trends.html нигде не читает TS.{source} — источник в SOURCES лишний"
        )


def _index_ids() -> set[str]:
    """id карточек из docs/data_index.json — то, чем страница их ищет."""
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    return {c["id"] for c in index["supplements"]}
