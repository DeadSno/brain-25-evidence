"""Контракт scripts/build_graph_data.py (PAGES_REVIEW п.20a).

Проверяет, что graph_data.json детерминированно генерируется из
data.json + effect_tags.json + graph_mech_edges.json и что
``--check`` проходит (идемпотентность).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_graph_data.py"
GRAPH = ROOT / "docs" / "graph_data.json"
MECH = ROOT / "docs" / "graph_mech_edges.json"

NODE_FIELDS = {"id", "label", "color", "font", "shape", "size", "title"}
EDGE_FIELDS = {"from", "to", "title", "width", "color"}


def _run(args):
    return subprocess.run(
        [sys.executable, str(BUILD)] + args,
        cwd=ROOT, capture_output=True, text=True,
    )


def _graph() -> dict:
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def _mech_edges() -> list[dict]:
    return json.loads(MECH.read_text(encoding="utf-8"))["edges"]


def test_idempotent_check_passes_twice():
    """Два прогона --check подряд → exit 0."""
    for _ in range(2):
        proc = _run(["--check"])
        assert proc.returncode == 0, (
            f"--check упал с кодом {proc.returncode}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def test_counts():
    g = _graph()
    nodes = g["nodes"]
    edges = g["edges"]
    mech = [e for e in edges if e["title"].startswith("механизм:")]
    tag = [e for e in edges if not e["title"].startswith("механизм:")]
    assert len(nodes) == 130, f"nodes={len(nodes)}"
    assert len(tag) == 1728, f"tag-edges={len(tag)}"
    assert len(mech) == 255, f"mech-edges={len(mech)}"
    assert len(edges) == 1983, f"total edges={len(edges)}"


def test_schema():
    g = _graph()
    for n in g["nodes"]:
        assert NODE_FIELDS <= set(n.keys()), f"node missing fields: {n['id']}"
        assert "group" not in n, f"node {n['id']} has forbidden field 'group'"
        assert isinstance(n["font"], dict) and n["font"] == {"color": "white"}
        assert n["shape"] == "dot"
        assert 10 <= n["size"] <= 50
    for e in g["edges"]:
        assert EDGE_FIELDS <= set(e.keys()), f"edge missing fields: {e}"


def test_nodes_sorted_by_id():
    g = _graph()
    ids = [n["id"] for n in g["nodes"]]
    assert ids == sorted(ids), "nodes не отсортированы по id"


def test_edges_sorted():
    g = _graph()
    pairs = [(e["from"], e["to"]) for e in g["edges"]]
    assert pairs == sorted(pairs), "рёбра не отсортированы по (from, to)"


def test_degree_in_title():
    """N в «Связей: N» равно реальной степени узла."""
    g = _graph()
    deg = {n["id"]: 0 for n in g["nodes"]}
    for e in g["edges"]:
        deg[e["from"]] = deg.get(e["from"], 0) + 1
        deg[e["to"]] = deg.get(e["to"], 0) + 1
    import re
    bad = []
    for n in g["nodes"]:
        m = re.search(r"Связей:\s*(\d+)", n["title"])
        n_deg = int(m.group(1)) if m else None
        if n_deg != deg.get(n["id"]):
            bad.append((n["id"], n_deg, deg.get(n["id"])))
    assert not bad, f"degree mismatch: {bad[:5]}"


def test_tag_edges_rule():
    """Все пары с общим тегом présentes; теги в title отсортированы."""
    data = json.loads(
        (ROOT / "docs" / "data.json").read_text(encoding="utf-8")
    )
    tags = json.loads(
        (ROOT / "docs" / "effect_tags.json").read_text(encoding="utf-8")
    )
    g = _graph()
    by_id = {rec["id"]: rec for rec in data}
    ids = sorted(by_id.keys())

    gen = set()
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            inter = set(tags.get(a, [])) & set(tags.get(b, []))
            if inter:
                gen.add((a, b))

    cur = set()
    for e in g["edges"]:
        if e["title"].startswith("теги:"):
            cur.add(tuple(sorted([e["from"], e["to"]])))
            inner = e["title"][len("теги:"):].strip()
            tgs = [x.strip() for x in inner.split(",")]
            assert tgs == sorted(tgs), f"теги не сортированы: {tgs}"

    assert cur == gen, (
        f"tag-edges не совпадают с правилом.\n"
        f"  cur-not-gen: {sorted(cur - gen)[:5]}\n"
        f"  gen-not-cur: {sorted(gen - cur)[:5]}"
    )


def test_mech_edges_preserved():
    """Все 255 curated мех-рёбра сохранены в graph_data.json."""
    g = _graph()
    mech_file = {(e["from"], e["to"], e["title"]) for e in _mech_edges()}
    mech_graph = {
        (e["from"], e["to"], e["title"])
        for e in g["edges"]
        if e["title"].startswith("механизм:")
    }
    assert mech_file == mech_graph, (
        f"мех-рёбра не совпадают с curated: "
        f"file={len(mech_file)} graph={len(mech_graph)}"
    )
