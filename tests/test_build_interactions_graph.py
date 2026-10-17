"""QA-P1-04: tests/test_build_interactions_graph.py

`scripts/build_interactions_graph.py` собирает `docs/interactions_graph.json`
— единственный источник данных для графа связей на `docs/interactions.html`.
Страница грузит файл одним `fetch` (interactions.html:1024) и при любой ошибке
рисует красную надпись «Не удалось загрузить interactions_graph.json»
(interactions.html:1037). То есть отказ генератора виден пользователю, а вот
тихая порча — другая история:

  * сломанная схема (нет `nodes`/`edges`) → `net.body` остаётся пустым,
    страница отдаёт ноль узлов и ноль рёбер БЕЗ ошибки;
  * `severity` вне набора {low, medium, high, critical} → в
    `SEV_ORDER[e.severity]` получается `undefined`, сравнение
    `SEV_ORDER[...] >= state.minSeverity` даёт `NaN` → ребро молча выпадает
    из графа (interactions.html:390);
  * `type` вне {synergy, antagonist, interaction} → `TYPE_COLOR[e.type]`
    даёт `undefined`, и страница падает на `hexAlpha(undefined)`;
  * пустой `severity`/`type` → легенда и подсветка не работают.

Всё это проверяется ниже на фикстуре из трёх карточек и на закоммиченном
файле. Точные количества рёбер и конкретные id НЕ проверяются: они меняются
вместе с data.json, и такой тест краснел бы на каждом обновлении данных.

Побочно тест ловит рассинхрон генератора с data.json через
`test_generator_is_deterministic` (две сборки из одного входа — байт в байт)
и через кросс-проверку набора severity с самим `interactions.html`
(`test_severity_set_matches_page`), а не через сравнение закоммиченного
файла с пересобранным: такой тест краснел бы на КАЖДОМ коммите, который
трогал data.json, и его пришлось бы чинить регенерацией артефакта. Это
отдельная задача, не молчаливая проверка.

Сеть не используется. Живой репозиторий тесты не трогают: генератор всегда
запускается на копии в tmp_path.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_interactions_graph.py"
COMMITTED = ROOT / "docs" / "interactions_graph.json"
PAGE = ROOT / "docs" / "interactions.html"

#: Режимы графа. Страница переключает их через setMode() и читает
#: state.data.<mode>.nodes / .edges (interactions.html:329,379).
MODES = ("supplements", "drugs")

#: Допустимые severity. Источник истины — SEV_ORDER / SEV_COLOR / SEV_ALPHA /
#: SEV_LABEL в interactions.html:208-219. Список продублирован здесь намеренно:
#: test_severity_set_matches_page следит, чтобы страница и тест не разошлись.
SEVERITIES = frozenset({"low", "medium", "high", "critical"})

#: Допустимые type. Источник истины — TYPE_COLOR / TYPE_LABEL
#: в interactions.html:217,220.
EDGE_TYPES = frozenset({"synergy", "antagonist", "interaction"})

#: Файл меньше этого — не «граф», а заглушка. Реальный файл ~50 КБ.
MIN_BYTES = 1024


# ── Фикстура входа: три карточки, покрывающие все три типа рёбер ───────────
#
# aaa ↔ bbb — взаимодействие (совпали по имени), плюс синергия и
# антагонизм; aaa → «варфарин» — взаимодействие с лекарством (в drugs-граф,
# в supplements-граф не попадает); ccc — карточка без связей.

RECORDS = [
    {
        "id": "aaa",
        "name": "ААА",
        "code": 1,
        "grade": "A",
        "interactions": [
            {"with": "БББ", "severity": "high", "note": "усиление"},
            {"with": "варфарин", "severity": "critical", "note": "риск кровотечения"},
        ],
        "synergists": ["БББ"],
        "antagonists": ["ААА"],
    },
    {"id": "bbb", "name": "БББ", "code": 2, "grade": "B",
     "interactions": [], "synergists": [], "antagonists": []},
    {"id": "ccc", "name": "ВВВ", "code": 3, "grade": "C",
     "interactions": [{"with": "ААА", "severity": "low", "note": ""}],
     "synergists": [], "antagonists": []},
]


def _base_env() -> dict:
    import os

    env = dict(os.environ)
    # Иначе дочерний Python на Windows возьмёт кодировку консоли (cp1251/cp866)
    # и русские сообщения генератора превратятся в «кракозябры».
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def make_repo(tmp_path: Path, records: list[dict]) -> Path:
    """Репозиторий с docs/data.json и копией генератора.

    Генератор берёт пути от __file__ (parents[1]), поэтому layout повторяет
    живой: scripts/build_interactions_graph.py + docs/data.json.
    """
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "docs" / "data.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copy(SCRIPT, root / "scripts" / SCRIPT.name)
    return root


def run_generator(root: Path, console_encoding: str = "utf-8") -> tuple[int, str]:
    """Запустить генератор в клоне. Возвращает (returncode, вывод).

    console_encoding — это PYTHONIOENCODING дочернего Python. По умолчанию
    utf-8 (см. _base_env), но тест legacy-консоли намеренно запускает
    генератор под cp1251.
    """
    env = _base_env()
    env["PYTHONIOENCODING"] = console_encoding
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / SCRIPT.name)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


def load_graph(root: Path) -> dict:
    """Разобрать собранный граф — с понятной ошибкой вместо JSONDecodeError."""
    out = root / "docs" / "interactions_graph.json"
    assert out.is_file(), f"генератор не создал {out.name}"
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.fixture()
def built(tmp_path):
    """Граф, собранный из RECORDS. Запуск падает здесь же, если rc != 0."""
    root = make_repo(tmp_path, RECORDS)
    rc, out = run_generator(root)
    assert rc == 0, f"генератор упал:\n{out}"
    return load_graph(root)


@pytest.fixture(scope="module")
def committed() -> dict:
    """Закоммиченный docs/interactions_graph.json — то, что реально грузит страница."""
    assert COMMITTED.is_file(), f"нет {COMMITTED.name} — страница покажет ошибку загрузки"
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


def assert_schema(graph: dict, mode: str, require_nonempty: bool) -> dict:
    """Проверки формы, общие для собранного и закоммиченного графа.

    require_nonempty=False для вырожденного входа: пустой data.json обязан
    дать валидный пустой граф, а не исключение.
    """
    assert mode in graph, f"в графе нет режима {mode!r}: {sorted(graph)}"
    part = graph[mode]
    assert isinstance(part, dict), f"{mode}: не объект, а {type(part).__name__}"
    for key in ("nodes", "edges"):
        assert key in part, f"{mode}: нет обязательного поля {key!r} (есть {sorted(part)})"
        assert isinstance(part[key], list), f"{mode}.{key} не список, а {type(part[key]).__name__}"
    if require_nonempty:
        assert part["nodes"], f"{mode}: 0 узлов — граф нечего рисовать"
        assert part["edges"], f"{mode}: 0 рёбер — граф нечего рисовать"
    return part


# ── Генератор на фикстуре ────────────────────────────────────────────────────


def test_generator_runs_without_errors(tmp_path):
    """Главный сценарий QA-P1-04: генератор обязан отработать и создать файл."""
    root = make_repo(tmp_path, RECORDS)
    rc, out = run_generator(root)
    assert rc == 0, out
    assert (root / "docs" / "interactions_graph.json").is_file(), out
    assert "[ok]" in out, f"генератор не отчитался об успехе:\n{out}"


def test_output_is_valid_json(built):
    """Файл читается json.loads. Обрыв записи = JSONDecodeError на странице."""
    assert isinstance(built, dict)
    assert set(built) == set(MODES), f"верхний уровень ждёт {MODES}, а в файле {sorted(built)}"


def test_schema_has_nodes_and_edges(built):
    for mode in MODES:
        assert_schema(built, mode, require_nonempty=True)


def test_graphs_not_empty(built):
    """Ни один режим не должен выродиться в пустой — иначе вкладка пустая."""
    for mode in MODES:
        part = built[mode]
        assert part["nodes"], f"{mode}: 0 узлов"
        assert part["edges"], f"{mode}: 0 рёбер"


def test_node_ids_unique(built):
    """Дубль id в vis.DataSet схлопывает узлы — сеть молча теряет вершины."""
    for mode in MODES:
        ids = [n["id"] for n in built[mode]["nodes"]]
        assert all(isinstance(i, str) and i for i in ids), f"{mode}: нестроковый или пустой id"
        dupes = {i for i in ids if ids.count(i) > 1}
        assert not dupes, f"{mode}: дубли id {sorted(dupes)}"


def test_edges_reference_existing_nodes(built):
    """Концы ребра обязаны быть в nodes: иначе vis-network не рисует ребро."""
    for mode in MODES:
        part = built[mode]["nodes"]
        ids = {n["id"] for n in part}
        for edge in built[mode]["edges"]:
            for key in ("from", "to"):
                assert key in edge, f"{mode}: ребро без поля {key!r}: {edge}"
                assert edge[key] in ids, (
                    f"{mode}: ребро ссылается на отсутствующую вершину "
                    f"{edge[key]!r} — vis-network её не нарисует"
                )


def test_severity_in_allowed_set(built):
    """Значение вне SEV_ORDER даёт undefined → NaN в фильтре (строка 390)."""
    for mode in MODES:
        for edge in built[mode]["edges"]:
            assert edge.get("severity") in SEVERITIES, (
                f"{mode}: неизвестный severity {edge.get('severity')!r} — "
                f"ребро выпадет из графа, допустимо {sorted(SEVERITIES)}"
            )


def test_type_in_allowed_set(built):
    """Значение вне TYPE_COLOR/TYPE_LABEL ломает цвет ребра."""
    for mode in MODES:
        for edge in built[mode]["edges"]:
            assert edge.get("type") in EDGE_TYPES, (
                f"{mode}: неизвестный type {edge.get('type')!r}, "
                f"допустимо {sorted(EDGE_TYPES)}"
            )


def test_nodes_carry_label(built):
    """Без label вершина рисуется пустым кружком (страница берёт n.label)."""
    for mode in MODES:
        for node in built[mode]["nodes"]:
            assert "id" in node, f"{mode}: узел без id: {node}"
            assert node.get("label"), f"{mode}: узел {node.get('id')!r} без label"


def test_drug_nodes_have_kind(built):
    """kind различает вершину-добавку и вершину-лекарство (interactions.html:459)."""
    kinds = {n.get("kind") for n in built["drugs"]["nodes"]}
    assert kinds <= {"supplement", "drug"}, f"drugs: неожиданный kind {sorted(map(str, kinds))}"
    assert kinds, "drugs: ни одного узла"


#: Маркер «взаимодействий нет». build_sup.py:55,110 знает его как NO_DATA /
#: NO_INTERACTION_MARK, graph_interactions.py:57 отфильтровывает сравнением.
#: Сгенерированный без этого узел-лекарство назывался бы «нет данных».
PLACEHOLDER = "нет данных"

PLACEHOLDER_RECORDS = [
    {"id": "aaa", "name": "ААА", "code": 1, "grade": "A",
     "interactions": [
         {"with": PLACEHOLDER, "severity": "medium", "note": "нет данных"},
         {"with": "варфарин", "severity": "high", "note": ""},
     ],
     "synergists": [], "antagonists": []},
    {"id": "bbb", "name": "БББ", "code": 2, "grade": "B",
     "interactions": [{"with": PLACEHOLDER, "severity": "medium", "note": ""}],
     "synergists": [], "antagonists": []},
]


def test_placeholder_target_is_not_a_node(tmp_path):
    """`with: "нет данных"` — маркер отсутствия, а не название лекарства.

    Без фильтра в графе появляется вершина «нет данных», к которой сходятся
    все рёбра таких карточек: на живых данных это 51 ребро, то есть треть
    графа лекарств называлась «нет данных». Замерено 2026-10-14.
    """
    root = make_repo(tmp_path, PLACEHOLDER_RECORDS)
    rc, out = run_generator(root)
    assert rc == 0, out
    graph = load_graph(root)
    for mode in MODES:
        ids = {n["id"] for n in graph[mode]["nodes"]}
        assert PLACEHOLDER not in ids, f"{mode}: маркер попал в узлы графа"
        hits = [e for e in graph[mode]["edges"]
                if e.get("to") == PLACEHOLDER or e.get("from") == PLACEHOLDER]
        assert not hits, f"{mode}: {len(hits)} рёбер уходят в маркер"


def test_card_with_only_placeholder_has_no_edges(tmp_path):
    """Карточка, у которой все взаимодействия — маркеры, в граф не попадает.

    Иначе висячая вершина: страница рисует её, но рёбер у неё нет.
    """
    root = make_repo(tmp_path, PLACEHOLDER_RECORDS)
    rc, out = run_generator(root)
    assert rc == 0, out
    graph = load_graph(root)
    for mode in MODES:
        assert "bbb" not in {n["id"] for n in graph[mode]["nodes"]}, (
            f"{mode}: карточка без реальных взаимодействий попала в граф"
        )


def test_runs_under_legacy_console_encoding(tmp_path):
    """Консоль cp1251 не знает «×» (0xD7 у неё — ÷).

    Без перенастройки stdout генератор падал UnicodeEncodeError ПОСЛЕ записи
    файла: артефакт на диске свежий, а код возврата 1. В pre-commit это
    выглядело бы как поломка репозитория. Замерено 2026-10-14.
    """
    root = make_repo(tmp_path, RECORDS)
    rc, out = run_generator(root, console_encoding="cp1251")
    assert rc == 0, f"генератор упал под cp1251:\n{out}"
    assert (root / "docs" / "interactions_graph.json").is_file()


def test_empty_input_yields_valid_empty_graph(tmp_path):
    """Пустой data.json обязан дать валидный ПУСТОЙ граф, а не исключение.

    Генератор ходит по c.get(...) через списки — KeyError на отсутствующих
    полях возможен, и падать он обязан не там, где его зовут по CI.
    """
    root = make_repo(tmp_path, [])
    rc, out = run_generator(root)
    assert rc == 0, out
    graph = load_graph(root)
    for mode in MODES:
        part = assert_schema(graph, mode, require_nonempty=False)
        assert part["nodes"] == [] and part["edges"] == []


def test_generator_is_deterministic(tmp_path):
    """Две сборки из одного входа — байт в байт.

    Порядок узлов идёт от порядка карточек в data.json, дедупликация —
    по порядку первого появления пары. Оба порядка детерминированы, так
    что расхождение означает нестабильность генератора (set/dict unordered),
    и артефакт в репозитории после такого коммита мерцал бы сам собой.
    """
    root = make_repo(tmp_path, RECORDS)
    rc, _ = run_generator(root)
    assert rc == 0
    first = (root / "docs" / "interactions_graph.json").read_bytes()
    rc, out = run_generator(root)
    assert rc == 0, out
    second = (root / "docs" / "interactions_graph.json").read_bytes()
    assert first == second, "две сборки из одного data.json разошлись"


# ── Закоммиченный артефакт: то, что реально грузит страница ─────────────────


@pytest.mark.parametrize("mode", MODES)
def test_committed_graph_schema(committed, mode):
    assert_schema(committed, mode, require_nonempty=True)


@pytest.mark.parametrize("mode", MODES)
def test_committed_graph_node_ids_unique(committed, mode):
    ids = [n["id"] for n in committed[mode]["nodes"]]
    assert all(ids), f"{mode}: пустой id в узлах"
    assert len(ids) == len(set(ids)), f"{mode}: {len(ids) - len(set(ids))} дублей id"


@pytest.mark.parametrize("mode", MODES)
def test_committed_graph_edges_resolve(committed, mode):
    ids = {n["id"] for n in committed[mode]["nodes"]}
    orphan = [
        (e.get("from"), e.get("to"))
        for e in committed[mode]["edges"]
        if e.get("from") not in ids or e.get("to") not in ids
    ]
    assert not orphan, f"{mode}: {len(orphan)} рёбер в пустоту, первые {orphan[:3]}"


@pytest.mark.parametrize("mode", MODES)
def test_committed_graph_severities_known(committed, mode):
    unknown = sorted({e.get("severity") for e in committed[mode]["edges"]} - SEVERITIES)
    assert not unknown, f"{mode}: неизвестные severity {unknown}"


@pytest.mark.parametrize("mode", MODES)
def test_committed_graph_types_known(committed, mode):
    unknown = sorted({e.get("type") for e in committed[mode]["edges"]} - EDGE_TYPES)
    assert not unknown, f"{mode}: неизвестные type {unknown}"


def test_committed_graph_has_no_placeholder(committed):
    """В закоммиченном графе нет вершины «нет данных» ни в одном режиме.

    Проверка на самом артефакте: она ловит возврат дефекта не только правкой
    генератора, но и новыми карточками в data.json (51 штука на 2026-10-14).
    """
    for mode in MODES:
        ids = {n["id"] for n in committed[mode]["nodes"]}
        assert PLACEHOLDER not in ids, (
            f"{mode}: в закоммиченном графе есть вершина-маркер {PLACEHOLDER!r}"
        )


def test_committed_file_not_truncated():
    """50 КБ → файл должен быть больше 1 КБ: заглушка прошла бы схему, но не размер."""
    size = COMMITTED.stat().st_size
    assert size > MIN_BYTES, f"{COMMITTED.name} — {size} Б, это не граф"


def test_severity_set_matches_page():
    """SEVERITIES должен совпадать с SEV_ORDER страницы.

    Страница фильтрует ребро по `SEV_ORDER[e.severity] >= state.minSeverity`
    (interactions.html:390). Новое значение в SEV_ORDER без правки теста —
    это молчаливое выпадение ребра из графа; новое значение в тесте без
    правки страницы — подмена ожиданий. Оба расхождения ловятся здесь.
    """
    html = PAGE.read_text(encoding="utf-8")
    m = re.search(r"const\s+SEV_ORDER\s*=\s*\{([^}]*)\}", html)
    assert m, "в interactions.html нет SEV_ORDER — фильтр severity не найден"
    page_keys = {
        k.split(":")[0].strip().strip("'\"")
        for k in m.group(1).split(",")
        if ":" in k
    }
    assert page_keys, "SEV_ORDER пуст — фильтр severity ничего не пропустит"
    assert page_keys == set(SEVERITIES), (
        f"набор severity разошёлся со страницей: страница {sorted(page_keys)}, "
        f"тест {sorted(SEVERITIES)}"
    )