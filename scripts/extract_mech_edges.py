"""Одноразовый экстракт curated мех-рёбер из docs/graph_data.json.

Читает docs/graph_data.json, фильтрует edges, у которых title начинается
с "механизм:", и пишет их в docs/graph_mech_edges.json как отдельный
управляемый вручную источник. Не перегенерируется build_graph_data.py.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DATA = ROOT / "docs" / "graph_data.json"
OUT = ROOT / "docs" / "graph_mech_edges.json"

EXPECTED_COUNT = 255

MECH_PREFIX = "механизм:"


def main() -> int:
    data = json.loads(GRAPH_DATA.read_text(encoding="utf-8"))
    edges = data.get("edges", [])

    mech_edges = []
    for edge in edges:
        title = edge.get("title", "")
        if isinstance(title, str) and title.startswith(MECH_PREFIX):
            mech_edges.append(
                {
                    "from": edge["from"],
                    "to": edge["to"],
                    "title": title,
                    "width": edge.get("width", 2.0),
                    "color": edge.get("color"),
                }
            )

    if len(mech_edges) != EXPECTED_COUNT:
        print(f"[!] ожидалось {EXPECTED_COUNT} мех-рёбер, найдено {len(mech_edges)}")
        return 1

    bad_titles = [e["title"] for e in mech_edges if not e["title"].startswith(MECH_PREFIX)]
    if bad_titles:
        print(f"[!] {len(bad_titles)} рёбер с некорректным title: {bad_titles[:5]}")
        return 1

    out = {
        "_комментарий": "Curated mech-edges. Manually maintained. Not regenerated "
        "by build_graph_data.py.",
        "_источник": f"extracted from graph_data.json at commit {_head_commit()}",
        "edges": mech_edges,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] записано {len(mech_edges)} мех-рёбер -> {OUT}")
    return 0


def _head_commit() -> str:
    import subprocess

    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
