"""Контракт API: сверка docs/api/v1/openapi.yaml с реальными ответами.

Закрывает QA_AUDIT P0-1, P0-2, P0-4, P0-5: до этого файл проверял 2 поля
из ~30 объявленных в спецификации (id и grade), из-за чего расхождения
verdict/enum, maxLength, minLength и maxItems жили в репозитории незамеченными.

Теперь спецификация читается программно, и каждый объявленный constraint
проверяется против данных. Откат любой правки в openapi.yaml или в данных
роняет тест.

PyYAML в окружении НЕТ (`import yaml` → ModuleNotFoundError; в .venv есть,
но тесты идут через ambient python), поэтому используется минимальный
парсер подмножества YAML, которого хватает для этого файла: вложенные
mapping'и, flow-списки `[a, b]`, block-списки `- item`, block-скaляры `|`/`>`.
Ни якорей, ни alias'ов, ни многострочных plain-скаляров в openapi.yaml нет.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "docs" / "api" / "v1"
OPENAPI = API / "openapi.yaml"


# ─────────────────────────── минимальный парсер YAML ───────────────────────────

_KEY_RE = re.compile(r"^([^:]+?):(?:\s+(.*))?$")


def _scalar(tok: str):
    tok = tok.strip()
    if tok in ("", "~", "null"):
        return None
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        return tok[1:-1]
    if tok in ("true", "True"):
        return True
    if tok in ("false", "False"):
        return False
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()
        return [_scalar(x) for x in _split_flow(inner)] if inner else []
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d+\.\d+", tok):
        return float(tok)
    return tok


def _split_flow(s: str):
    """Разбить 'a, "b, c", d' по запятым верхнего уровня, уважая кавычки."""
    out, cur, quote = [], [], None
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch == ",":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def _rows(text: str):
    return [(len(r) - len(r.lstrip()), r.strip())
            for r in text.split("\n")
            if r.strip() and not r.lstrip().startswith("#")]


def _parse_yaml(text: str):
    rows = _rows(text)
    pos = 0

    def block(indent):
        nonlocal pos
        if pos >= len(rows):
            return None
        if rows[pos][1].startswith("- "):
            seq = []
            while pos < len(rows) and rows[pos][0] == indent and rows[pos][1].startswith("- "):
                item = rows[pos][1][2:]
                if _KEY_RE.match(item):
                    # Элемент-словарь: "- key: value" плюс продолжение на indent+2.
                    # Виртуально поднимаем отступ, иначе block() съест только
                    # первую строку и весь остальной документ останется неразобранным.
                    rows[pos] = (indent + 2, item)
                    seq.append(block(indent + 2))
                else:
                    seq.append(_scalar(item))
                    pos += 1
            return seq
        out = {}
        while pos < len(rows) and rows[pos][0] == indent:
            _, line = rows[pos]
            m = _KEY_RE.match(line)
            if not m:
                break
            key, val = m.group(1).strip(), (m.group(2) or "").strip()
            pos += 1
            if val[:1] in ("|", ">"):
                buf = []
                while pos < len(rows) and rows[pos][0] > indent:
                    buf.append(rows[pos][1])
                    pos += 1
                out[key] = "\n".join(buf)
            elif val == "":
                out[key] = block(rows[pos][0]) if pos < len(rows) and rows[pos][0] > indent else None
            else:
                out[key] = _scalar(val)
        return out

    return block(rows[0][0]) if rows else {}


# ─────────────────────────────── загрузка данных ───────────────────────────────

@pytest.fixture(scope="module")
def spec():
    doc = _parse_yaml(OPENAPI.read_text(encoding="utf-8"))
    assert isinstance(doc, dict) and "components" in doc, "openapi.yaml не распарсен"
    return doc


@pytest.fixture(scope="module")
def schemas(spec):
    return spec["components"]["schemas"]


@pytest.fixture(scope="module")
def index():
    return json.loads((API / "index.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def payload():
    return json.loads((API / "supplements.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def supplements(payload):
    return payload["supplements"]


def _deref(node, schemas):
    """Разрешить $ref в '#/components/schemas/X' (OpenAPI 3.0 — только локальные)."""
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 10:
        seen += 1
        name = node["$ref"].rsplit("/", 1)[-1]
        node = schemas[name]
    return node


# ────────────────────────────── проверка одного поля ────────────────────────────

_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "array": list,
    "object": dict,
    "boolean": bool,
}


def _check_value(value, sch, schemas, where, errors):
    """Проверить одно значение против схемы. Копит ошибки в errors."""
    sch = _deref(sch, schemas)
    if not isinstance(sch, dict) or "type" not in sch:
        return

    # OpenAPI 3.0: nullable: true разрешает явный null вместо type
    if value is None:
        if not sch.get("nullable"):
            errors.append(f"{where}: null, но поле не объявлено nullable")
        return

    want = _TYPES.get(sch["type"])
    if want is not None:
        # bool — подтип int в Python, проверяем отдельно чтобы не пропустить
        if sch["type"] == "integer" and isinstance(value, bool):
            errors.append(f"{where}: тип boolean вместо integer")
        elif not isinstance(value, want):
            errors.append(f"{where}: тип {type(value).__name__} вместо {sch['type']}")
            return

    if "enum" in sch and value not in sch["enum"]:
        errors.append(f"{where}: значение {value!r} не в enum {sch['enum']!r}")

    if isinstance(value, str):
        if "minLength" in sch and len(value) < sch["minLength"]:
            errors.append(f"{where}: длина {len(value)} < minLength {sch['minLength']}")
        if "maxLength" in sch and len(value) > sch["maxLength"]:
            errors.append(f"{where}: длина {len(value)} > maxLength {sch['maxLength']}")
        if "pattern" in sch and not re.search(sch["pattern"], value):
            errors.append(f"{where}: {value!r} не матчит pattern {sch['pattern']!r}")

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in sch and value < sch["minimum"]:
            errors.append(f"{where}: {value} < minimum {sch['minimum']}")
        if "maximum" in sch and value > sch["maximum"]:
            errors.append(f"{where}: {value} > maximum {sch['maximum']}")

    if isinstance(value, list):
        if "minItems" in sch and len(value) < sch["minItems"]:
            errors.append(f"{where}: {len(value)} элементов < minItems {sch['minItems']}")
        if "maxItems" in sch and len(value) > sch["maxItems"]:
            errors.append(f"{where}: {len(value)} элементов > maxItems {sch['maxItems']}")
        if isinstance(sch.get("items"), dict):
            for i, item in enumerate(value):
                _check_value(item, sch["items"], schemas, f"{where}[{i}]", errors)


def _check_object(obj, sch, schemas, where, errors, only=None):
    """Проверить объект против схемы: required + каждое объявленное свойство."""
    sch = _deref(sch, schemas)
    for key in sch.get("required") or []:
        if key not in obj:
            errors.append(f"{where}: отсутствует обязательное поле {key!r}")
    props = sch.get("properties") or {}
    for key, sub in props.items():
        if only is not None and key not in only:
            continue
        if key not in obj:
            continue
        _check_value(obj[key], sub, schemas, f"{where}.{key}", errors)


# ──────────────────────────────────── тесты ─────────────────────────────────────

def test_api_dir_exists():
    assert API.exists(), f"{API} не создан"


def test_index_json_exists():
    assert (API / "index.json").exists(), "index.json не создан"


def test_supplements_json_exists():
    assert (API / "supplements.json").exists(), "supplements.json не создан"


def test_openapi_exists():
    assert OPENAPI.exists(), "openapi.yaml не создан"


def test_postman_collection_exists():
    assert (API / "postman_collection.json").exists(), "postman_collection.json не создан"


def test_openapi_parses(spec):
    """Парсер обязан разобрать документ целиком, а не только верхний уровень."""
    assert spec["openapi"].startswith("3.")
    assert set(spec["paths"]) == {"/api/v1/index.json", "/api/v1/supplements.json"}
    assert len(spec["servers"]) == 2, "servers — список словарей, а не плоских строк"
    for name in ("ApiIndex", "Stats", "SupplementsPayload", "Supplement",
                 "Interaction", "KeySource", "Error"):
        assert name in spec["components"]["schemas"], f"нет схемы {name}"


def test_index_structure(index):
    for f in ["version", "count", "stats", "ids"]:
        assert f in index, f"index.json нет {f}"
    assert index["count"] == 130
    assert len(index["ids"]) == 130


def test_supplements_structure(supplements):
    assert len(supplements) == 130
    for s in supplements:
        for f in ["id", "grade"]:
            assert f in s, f"supplement нет {f}"


def test_grades_in_index(index):
    grades = index["stats"]["grades"]
    total = sum(grades.values())
    assert total == 130, f"сумма grades={total}, ожидалось 130"


# ── QA_AUDIT P0-1: enum сверяется со СПЕЦИФИКАЦИЕЙ, а не с захардкоженным списком ──

def test_verdict_enum_matches_spec(schemas, supplements):
    """Если openapi.yaml разойдётся с данными по verdict — падаем здесь.

    Именно этот тест должен был поймать P0-1: раньше enum нигде не сверялся.
    """
    enum = _deref(schemas["Supplement"]["properties"]["verdict"], schemas)["enum"]
    got = sorted({s["verdict"] for s in supplements})
    assert got == sorted(enum), (
        f"verdict в данных {got} != enum в openapi.yaml {sorted(enum)}. "
        "Данные — источник правды, приводи openapi.yaml."
    )


def test_grade_enum_matches_spec(schemas, supplements):
    enum = _deref(schemas["Supplement"]["properties"]["grade"], schemas)["enum"]
    got = sorted({s["grade"] for s in supplements})
    assert got == sorted(enum), f"grade {got} != enum {sorted(enum)}"


# ──────────────────── полная сверка каждой объявленной схемы ────────────────────

def test_supplements_payload_matches_openapi(schemas, payload):
    """SupplementsPayload + все вложенные схемы, включая Supplement целиком."""
    errors = []
    _check_object(payload, schemas["SupplementsPayload"], schemas, "payload", errors)
    # ограничения уровня payload
    if payload["count"] != len(payload["supplements"]):
        errors.append(f"payload.count={payload['count']} != len(supplements)={len(payload['supplements'])}")
    for s in payload["supplements"]:
        _check_object(s, schemas["Supplement"], schemas, f"sup[{s.get('id')}]", errors)
    assert not errors, "Нарушения SupplementsPayload/Supplement:\n  " + "\n  ".join(errors[:40])


def test_api_index_matches_openapi(schemas, index):
    errors = []
    _check_object(index, schemas["ApiIndex"], schemas, "index", errors)
    if index["count"] != len(index["ids"]):
        errors.append(f"index.count={index['count']} != len(ids)={len(index['ids'])}")
    assert not errors, "Нарушения ApiIndex:\n  " + "\n  ".join(errors[:40])


def test_key_sources_max_items(schemas, supplements):
    """QA_AUDIT P0-2. Ловит и заниженный maxItems, и реальное превышение."""
    spec_max = _deref(schemas["Supplement"]["properties"]["key_sources"], schemas)["maxItems"]
    worst = max(len(s.get("key_sources", [])) for s in supplements)
    assert worst <= spec_max, (
        f"key_sources: в данных максимум {worst}, а openapi.yaml объявляет maxItems: {spec_max}"
    )


def test_about_max_length(schemas, supplements):
    """QA_AUDIT P0-4: «Сульфорафан» = 183 символа при старом maxLength 160."""
    spec_max = _deref(schemas["Supplement"]["properties"]["about"], schemas)["maxLength"]
    worst = max((len(s["about"]), s["id"]) for s in supplements if isinstance(s.get("about"), str))
    assert worst[0] <= spec_max, (
        f"about: самая длинная — {worst[1]} ({worst[0]} симв.) при maxLength: {spec_max}"
    )


def test_effects_min_length(schemas, supplements):
    """QA_AUDIT P0-5: эффект «Сон» = 3 символа при старом minLength 5."""
    spec_min = _deref(schemas["Supplement"]["properties"]["effects"], schemas)["items"]["minLength"]
    for s in supplements:
        for e in s.get("effects", []):
            assert len(e) >= spec_min, (
                f"{s['id']}: эффект {e!r} = {len(e)} симв. < minLength {spec_min}"
            )


def test_pmid_pattern(schemas, supplements):
    """KeySource.pmid: pattern ^[0-9]+$ — строка, не число."""
    pat = _deref(schemas["Supplement"]["properties"]["key_sources"], schemas)
    pat = _deref(pat["items"], schemas)["properties"]["pmid"]["pattern"]
    for s in supplements:
        for k in s.get("key_sources", []):
            assert re.fullmatch(pat, str(k["pmid"])), f"{s['id']}: pmid={k['pmid']!r} !~ {pat}"


def test_interaction_severity_enum(schemas, supplements):
    enum = _deref(_deref(schemas["Supplement"]["properties"]["interactions"], schemas)["items"],
                  schemas)["properties"]["severity"]["enum"]
    for s in supplements:
        for i in s.get("interactions", []):
            assert i["severity"] in enum, f"{s['id']}: severity={i['severity']!r} не в {enum}"


# ─────────────── каждое ограничение openapi.yaml проверяется параметризованно ───────────────

def _collect_constraints(schemas, prefix, node, acc):
    """Обойти схему и собрать (человекочитаемый путь, constraint) для всех полей."""
    node = _deref(node, schemas)
    if not isinstance(node, dict):
        return
    for c in ("enum", "pattern", "minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum"):
        if c in node and node[c] is not None:
            acc.append((f"{prefix}[{c}]", node[c]))
    for key, sub in (node.get("properties") or {}).items():
        _collect_constraints(schemas, f"{prefix}.{key}", sub, acc)
    items = node.get("items")
    if isinstance(items, dict):
        _collect_constraints(schemas, f"{prefix}[]", items, acc)


@pytest.mark.parametrize("field", [
    "verdict", "grade", "code", "about", "who_needs", "onset", "myths",
    "food_sources", "guidelines", "how_to_choose", "effects", "mechs",
    "key_sources", "scienceIndex", "rct", "metaCount", "citations",
])
def test_every_declared_constraint_holds(schemas, supplements, field):
    """Для каждого ограничения, объявленного в openapi.yaml — проверка данных.

    Путь вида "verdict[enum]" означает: enum поля verdict. "effects[][minLength]" —
    minLength каждого элемента массива effects. Тест падает, если нарушение есть.
    """
    sch = _deref(schemas["Supplement"]["properties"], schemas)
    assert field in sch, f"в openapi.yaml нет свойства {field}"
    # У поля должен быть объявлен хотя бы type — иначе проверять нечего.
    # Ограничения значений (enum/length/items/min/max) могут отсутствовать
    # legitimately: у scienceIndex/rct/metaCount в спеке только type + description.
    node = _deref(sch[field], schemas)
    assert "type" in node, f"у {field} в openapi.yaml нет type — нечего проверять"
    constraints = []
    _collect_constraints(schemas, field, sch[field], constraints)

    errors = []
    for s in supplements:
        if field not in s:
            errors.append(f"{s['id']}: нет поля {field}")
            continue
        _check_value(s[field], sch[field], schemas, field, errors)
    assert not errors, (
        f"Нарушения по {field} (ограничения из openapi.yaml: {constraints or 'только type'}):\n  "
        + "\n  ".join(errors[:20])
    )


def test_required_fields_present(schemas, supplements):
    required = _deref(schemas["Supplement"], schemas)["required"]
    missing = [(s.get("id"), f) for s in supplements for f in required if f not in s]
    assert not missing, f"отсутствуют required-поля: {missing[:10]}"
