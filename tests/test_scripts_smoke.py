"""QA-P1-05: tests/test_scripts_smoke.py

Дымовой прогон 11 скриптов из `scripts/`: компилируются, импортируются без
сети, отвечают на `--help`, не падают на минимальном входе.

Это SMOKE, а не функциональные тесты. Здесь нет проверки того, что скрипт
считает ПРАВИЛЬНО: значение, формула и полнота разбора — террито
отдельных тестов (`test_build_timeseries.py`, `test_build_interactions_graph.py`,
`test_slim_fixtures.py` и т. д.). Здесь только «скрипт жив и не падает» —
ровно та поломка, которая иначе обнаруживается вручную, через месяц, на
свежем клоне.

Что и почему проверяется на каждый скрипт:

  * `test_script_compiles` — синтаксис под текущим интерпретатором. Дёшево,
    ловит опечатку до запуска чего-либо.
  * `test_script_imports_without_network` — импорт НЕ должен ходить в сеть.
    Проверка не на глаз: дочерний процесс запускается с заглушкой `socket`,
    и любой реальный запрос поднимет AssertionError. Скрипты, у которых нет
    `if __name__ == "__main__"`, при импорте выполняются целиком —
    `build_changelog_public.py` читает CHANGELOG.md и пишет артефакт
    (строки 12-24, 81). Это не дефект самого скрипта (его так запускают),
    но импортировать его в живом репозитории нельзя, поэтому такие
    скрипты помечены xfail и проверяются только в клоне.
  * `test_script_runs_on_minimal_input` — запуск с минимальным входом должен
    завершиться rc=0 и создать ожидаемый артефакт. Вход — копия в tmp,
    живой репозиторий тесты не трогают.
  * `test_help_works` — `--help` у argparse-скриптов (6 из 11). Скрипт без
    argparse на `--help` его не понимает и просто выполнится, поэтому такие
    проверяются только на отсутствие необъявленных флагов.
  * `test_required_argument_is_reported` — скрипт с обязательным аргументом,
    запущенный без него, обязан упасть с кодом 2 и назвать сам аргумент.
    Молчаливый выход 0 означал бы, что скрипт отработал не тот сценарий.
  * `test_documented_flags_exist` — флаги из блока «Использование» в
    docstring обязаны быть объявлены в argparse. Расхождение означает, что
    человек прочитает инструкцию и запустит не то.

`recalc_science_index.py` без флагов идёт в PubMed (esearch на каждую
карточку), поэтому он запускается только с `--help`. Найденное при этом
расхождение инструкции и argparse — см. `test_recalc_documented_dry_run`,
это единственный известный долг в этом файле.
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

#: Минимальный JATS-XML для parse_xml_meta: корневой <article> обязателен
#: (парсер берёт funding/coi через root.iter), содержимое — произвольное.
MINI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article>
    <front>
      <article-meta>
        <abstract><p>Test abstract about magnesium and sleep.</p></abstract>
      </article-meta>
    </front>
    <back>
      <ack><p>This work was funded by the National Institutes of Health.</p></ack>
    </back>
  </article>
</pmc-articleset>
"""

#: Минимальный src/config.py для add_supplements_batch: скрипт вставляет
#: запись в SUPPLEMENTS регуляркой, и ей нужен формат «"Имя": "term",».
MINI_CONFIG = '''# -*- coding: utf-8 -*-
"""Минимальная копия для smoke-теста."""

SUPPLEMENTS = {
    "Креатин": "creatine",
    "Магний": "magnesium",
}
'''

#: CSV для add_supplements_batch --dry-run: категория из CATEGORIES,
#: имя новой (нет ни в data.json, ни в config.py), query непустой.
MINI_CSV = "name,term,category,query,code\nШатавари,Asparagus racemosus,Общее,(Asparagus racemosus),0\n"

#: Заглушка сокета для проверки «импорт не ходит в сеть». Подставляется
#: через python -c, поэтому единственная точка входа — сюда.
#:
#: Подменяется НЕ класс socket.socket, а три функции: класс ssl.SSLSocket
#: наследуется от socket.socket, и подмена класса ломает `import ssl`
#: (TypeError: function() argument 'code' must be code, not str), а он
#: тянется за urllib.request — то есть за половиной скриптов.
NO_NETWORK = """
import socket


def _blocked(*args, **kwargs):
    raise AssertionError("smoke-тест: скрипт полез в сеть при импорте")


socket.socket.connect = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked
"""


#: Описание одного скрипта для smoke-прогона.
#:   name            — имя файла без .py
#:   files           — фикстуры: путь относительно клона → содержимое
#:   dirs            — каталоги, которые должны существовать
#:   args            — argv для проверки запуска (None = запуск пропускается)
#:   artifact        — файл, который обязан появиться после запуска
#:   required_arg    — обязательный аргумент argparse, если есть
#:   side_effect_on_import — True, если скрипт выполняется при импорте
#:   skip_run_reason — почему запуск не проверяется
SMOKE = [
    {
        "name": "build_changelog_public",
        "files": {"CHANGELOG.md": "# Changelog\n\n## [5.6.0] — 2026-10-14\n- Запись\n"},
        "dirs": ["docs"],
        "artifact": "docs/changelog_public.html",
        "side_effect_on_import": True,
    },
    {
        "name": "add_supplements_batch",
        "files": {
            "docs/data.json": "[]",
            "docs/data_pubmed_terms.json": "{}",
            "src/config.py": MINI_CONFIG,
            "scripts/add.csv": MINI_CSV,
        },
        "dirs": ["docs", "src"],
        "args": ["--input", "scripts/add.csv", "--dry-run"],
        "required_arg": "--input",
    },
    {
        "name": "apply_drafts",
        "files": {"docs/data.json": "[]"},
        "dirs": ["docs"],
        "args": ["--check"],
    },
    {
        "name": "recalc_science_index",
        "files": {"docs/data.json": "[]", "docs/data_pubmed_terms.json": "{}"},
        "dirs": ["docs", "reports"],
        # Без флагов скрипт делает esearch к PubMed на каждую карточку.
        "args": None,
        "skip_run_reason": "без флагов ходит в PubMed (esearch на карточку)",
    },
    {
        "name": "rebuild_index",
        "files": {"data/pmc/text/99999999.xml": MINI_XML},
        "dirs": ["data/pmc/text"],
        "artifact": "data/pmc/index.json",
    },
    {
        "name": "parse_dosages",
        "files": {"docs/data.json": "[]"},
        "dirs": ["docs"],
        "artifact": "docs/dosage_parsed.json",
    },
    {
        "name": "parse_xml_meta",
        "files": {"data/pmc/text/99999999.xml": MINI_XML},
        "dirs": ["data/pmc/text", "data/papers"],
        "artifact": "data/processed/xml_meta.json",
    },
    {
        "name": "validate_proposal",
        "files": {"docs/data.json": "[]"},
        "dirs": ["docs"],
        # Схема proposal-файла не описана как контракт; проверять её —
        # функциональный тест. Здесь только синтаксис CLI.
        "args": None,
        "skip_run_reason": "требует proposal-файл по внутреннему контракту",
        "required_arg": "--proposal",
    },
    {
        "name": "extract_g",
        "files": {},
        "dirs": [],
        "args": [],
    },
    {
        "name": "extract_sample_sizes",
        "files": {"data/papers/papers.json": "{}"},
        "dirs": ["data/papers"],
        "artifact": "data/papers/sample_sizes.json",
    },
    {
        "name": "extract_stats_claims",
        "files": {"data/papers/papers.json": "{}"},
        "dirs": ["data/papers"],
        "artifact": "data/papers/stats_claims.json",
    },
]

IDS = [s["name"] for s in SMOKE]
BY_NAME = {s["name"]: s for s in SMOKE}
#: Скрипты с обязательным аргументом: без него падают с кодом 2.
WITH_REQUIRED = [s["name"] for s in SMOKE if "required_arg" in s]


def _env() -> dict:
    env = dict(os.environ)
    # Русские сообщения скриптов иначе уедут в кодировку консоли cp1251/cp866.
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def make_clone(spec: dict, tmp_path: Path) -> Path:
    """Репозиторий с одним скриптом и его минимальным входом.

    Скрипты берут пути от Path(__file__).parents[1], поэтому раскладка
    повторяет живую. Копия нужна, чтобы прогон не писал в рабочее дерево:
    build_changelog_public заново создаёт docs/changelog_public.html,
    а parse_dosages и extract_* пишут свои артефакты.
    """
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPTS / f"{spec['name']}.py", root / "scripts" / f"{spec['name']}.py")
    for rel in spec.get("dirs", []):
        (root / rel).mkdir(parents=True, exist_ok=True)
    for rel, content in spec.get("files", {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def run_script(spec: dict, root: Path, args: list[str] | None = None) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(root / "scripts" / f"{spec['name']}.py")]
    argv += list(spec.get("args") or [] if args is None else args)
    return subprocess.run(
        argv, cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=_env(),
    )


def snapshot(root: Path) -> set[str]:
    """Файлы клона без __pycache__: импорт всегда пишет .pyc, это не запись скрипта."""
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def source(name: str) -> str:
    return (SCRIPTS / f"{name}.py").read_text(encoding="utf-8")


def declared_flags(name: str) -> set[str]:
    """Флаги, объявленные через argparse."""
    return set(re.findall(r"add_argument\(\s*['\"](--?[\w-]+)", source(name)))


def documented_flags(name: str) -> set[str]:
    """Флаги из блока «Использование» / примеров команд в docstring."""
    doc = ast.get_docstring(ast.parse(source(name))) or ""
    return set(re.findall(r"(?<![\w-])(--[a-z][\w-]*)", doc))


#: Скрипты с argparse — по факту объявленных флагов, а не по таблице.
#: Таблица может разойтись с кодом (скрипт добавили флаг и забыли внести),
#: и тогда --help перестанет проверяться именно у того, у кого он есть.
#: 6 из 11: build_changelog_public, extract_g, parse_dosages, parse_xml_meta,
#: rebuild_index argparse не используют.
WITH_CLI = [name for name in IDS if declared_flags(name)]


# ── Компиляция ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", IDS)
def test_script_compiles(name):
    """Синтаксис под текущим интерпретатором — самая дешёвая проверка."""
    src = source(name)
    compile(src, str(SCRIPTS / f"{name}.py"), "exec")


@pytest.mark.parametrize("name", IDS)
def test_script_has_no_top_level_syntax_error(name):
    """ast.parse ловит несовместимый с версией синтаксис до запуска."""
    ast.parse(source(name))


# ── Импорт ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    [s["name"] for s in SMOKE if s.get("side_effect_on_import")],
)
@pytest.mark.xfail(
    reason="скрипт выполняется при импорте (нет if __name__ == '__main__'): "
           "build_changelog_public.py читает CHANGELOG.md и пишет артефакт "
           "при импорте — это by design, но импортировать его нельзя",
    strict=True,
)
def test_import_is_side_effect_free(name, tmp_path):
    """Импорт скрипта не должен ничего писать и никуда ходить."""
    root = make_clone(BY_NAME[name], tmp_path)
    before = snapshot(root)
    code = NO_NETWORK + f"\nimport sys\nsys.path.insert(0, r'{root / 'scripts'}')\nimport {name}\n"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    created = snapshot(root) - before
    assert not created, f"импорт {name} создал файлы: {sorted(created)}"


@pytest.mark.parametrize(
    "name", [s["name"] for s in SMOKE if not s.get("side_effect_on_import")]
)
def test_script_imports_without_network(name, tmp_path):
    """Импорт проходит без сети и без записи на диск.

    Сокет заглушен: скрипт, который при импорте дёрнет PubMed, упадёт с
    AssertionError, а не отработает молча.
    """
    root = make_clone(BY_NAME[name], tmp_path)
    before = snapshot(root)
    code = NO_NETWORK + f"\nimport sys\nsys.path.insert(0, r'{root / 'scripts'}')\nimport {name}\n"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=_env(),
    )
    assert proc.returncode == 0, (
        f"импорт {name} упал (возможно, поход в сеть при импорте):\n"
        f"{proc.stdout}\n{proc.stderr}"
    )
    created = snapshot(root) - before
    assert not created, f"импорт {name} создал файлы: {sorted(created)}"


# ── Запуск ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", [s["name"] for s in SMOKE if s.get("args", []) is not None])
def test_script_runs_on_minimal_input(name, tmp_path):
    """Запуск на минимальном входе: rc=0 и ожидаемый артефакт на месте."""
    spec = BY_NAME[name]
    root = make_clone(spec, tmp_path)
    proc = run_script(spec, root)
    assert proc.returncode == 0, (
        f"{name} упал (rc={proc.returncode}) на минимальном входе:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )
    if spec.get("artifact"):
        assert (root / spec["artifact"]).is_file(), (
            f"{name} отработал, но {spec['artifact']} не создал"
        )
    elif spec["args"]:
        # extract_g — библиотека функций: при запуске как скрипт молчит,
        # и это нормально. Остальные обязаны отчитаться об успехе.
        assert "[OK]" in proc.stdout or "[DRY-RUN]" in proc.stdout, (
            f"{name} не отчитался об успехе:\n{proc.stdout}"
        )


@pytest.mark.parametrize("name", [s["name"] for s in SMOKE if s.get("skip_run_reason")])
def test_script_run_is_skipped_deliberately(name):
    """Скрипты, которые нельзя гонять в smoke, объявлены как таковые.

    Иначе «пропущено» выглядело бы так же, как «проверено»: pytest
    показывает пропуски отдельной строкой, а здесь их нет вообще.
    """
    assert BY_NAME[name]["args"] is None
    assert BY_NAME[name].get("skip_run_reason"), "причина пропуска обязательна"


@pytest.mark.parametrize(
    "name",
    [s["name"] for s in SMOKE
     if str(s.get("artifact", "")).endswith(".json") and s.get("args", []) is not None],
)
def test_artifact_is_valid_json(name, tmp_path):
    """Артефакт скрипта — валидный JSON, а не обрывок."""
    spec = BY_NAME[name]
    root = make_clone(spec, tmp_path)
    proc = run_script(spec, root)
    assert proc.returncode == 0, proc.stderr
    json.loads((root / spec["artifact"]).read_text(encoding="utf-8"))


# ── CLI ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", WITH_CLI)
def test_help_works(name, tmp_path):
    """`--help` обязан печатать usage и выходить с 0.

    Скрипт, который на `--help` падает или уходит в работу, нельзя
    безопасно вызывать из документации.
    """
    spec = BY_NAME[name]
    root = make_clone(spec, tmp_path)
    proc = run_script(spec, root, args=["--help"])
    assert proc.returncode == 0, (
        f"{name} --help упал (rc={proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    )
    assert "usage" in (proc.stdout + proc.stderr).lower(), (
        f"{name} --help не напечатал usage:\n{proc.stdout}"
    )
    for flag in declared_flags(name):
        assert flag in proc.stdout, f"{name} --help не упоминает свой флаг {flag}"


@pytest.mark.parametrize("name", WITH_REQUIRED)
def test_required_argument_is_reported(name, tmp_path):
    """Без обязательного аргумента — код 2 и имя аргумента в сообщении."""
    spec = BY_NAME[name]
    root = make_clone(spec, tmp_path)
    proc = run_script(spec, root, args=[])
    assert proc.returncode == 2, (
        f"{name} без {spec['required_arg']} вернул {proc.returncode}, а не 2 — "
        f"значит, отработал не тот сценарий:\n{proc.stdout}"
    )
    assert spec["required_arg"] in proc.stderr, (
        f"{name} не назвал обязательный аргумент {spec['required_arg']}:\n{proc.stderr}"
    )


@pytest.mark.parametrize("name", [s["name"] for s in SMOKE if s.get("artifact") or s.get("args")])
def test_documented_flags_exist(name):
    """Флаги из инструкции в docstring объявлены в argparse.

    Расхождение безвредно только на бумаге: человек читает «--dry-run»,
    запускает — и получает либо ошибку разбора, либо (хуже) реальную запись
    в данные вместо пробного прогона.
    """
    missing = documented_flags(name) - declared_flags(name)
    assert not missing, (
        f"{name}: инструкция упоминает {sorted(missing)}, которых нет в argparse"
    )


def test_recalc_documented_dry_run():
    """Единственный известный долг: recalc_science_index обещает --dry-run.

    Docstring (строки 9-11) показывает `--dry-run`, argparse объявляет
    только `--apply`. На практике скрипт без флагов и есть dry-run —
    он читает PubMed и печатает отчёт, не записывая data.json. То есть
    инструкция вводит в заблуждение, но данные не портит.

    strict=True: если `--dry-run` объявят, тест упадёт с XPASS и маркер
    придётся снять.
    """
    name = "recalc_science_index"
    assert "--dry-run" in documented_flags(name)
    assert "--dry-run" not in declared_flags(name), (
        "--dry-run уже объявлен — сними xfail и поправь docstring"
    )


def test_add_supplements_dry_run_writes_nothing(tmp_path):
    """`--dry-run` обязан не трогать файлы, а не просто печатать «не изменены».

    Обещание в stdout проверяем по факту: сравниваем байты config.py,
    data_pubmed_terms.json и data.json до и после, и смотрим, что бэкапы
    *.bak не появились. Бэкапы в add_supplements_batch создаются ПОСЛЕ
    ветки dry_run (строки 183-185), поэтому их отсутствие — тоже часть
    контракта.
    """
    spec = BY_NAME["add_supplements_batch"]
    root = make_clone(spec, tmp_path)
    watched = ["src/config.py", "docs/data_pubmed_terms.json", "docs/data.json"]
    before = {rel: (root / rel).read_bytes() for rel in watched}
    proc = run_script(spec, root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[DRY-RUN]" in proc.stdout, f"dry-run не отметился:\n{proc.stdout}"
    for rel in watched:
        assert (root / rel).read_bytes() == before[rel], f"dry-run изменил {rel}"
    assert not list(root.rglob("*.bak")), "dry-run создал бэкапы"


def test_smoke_table_matches_disk():
    """Таблица smoke не должна разъезжаться с диском: все 11 файлов на месте."""
    for name in IDS:
        assert (SCRIPTS / f"{name}.py").is_file(), f"нет scripts/{name}.py"
    on_disk = {p.stem for p in SCRIPTS.glob("*.py")} & set(IDS)
    assert on_disk == set(IDS), f"в таблице лишние: {set(IDS) - on_disk}"