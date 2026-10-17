"""Генерирует docs/graph_positions.json — детерминированную круглую
раскладку узлов графа (PAGES_REVIEW п.20b).

Вход:  docs/graph_data.json (узлы, отсортированные по id)
Выход: docs/graph_positions.json со структурой, совместимой с текущей:

    {
      "_комментарий": "...",
      "_источники": "...",
      "layouts": {
        "graph": {
          "center": [0.5, 0.5],
          "scale": 1.0,
          "count": N,
          "positions": {
            "<id>": {"nx": ..., "ny": ..., "fixed": true},
            ...
          }
        }
      }
    }

Формула (детерминированная, sort by id):
  angle_i = 2π · i / N
  nx = 0.5 + 0.5 · cos(angle_i)
  ny = 0.5 + 0.5 · sin(angle_i)

nx, ny нормализованы в [0, 1]. fixed = true для всех.

Флаги:
  --check  не пишет файл, сравнивает с текущим, exit 1 при diff
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DATA = ROOT / "docs" / "graph_data.json"
OUT = ROOT / "docs" / "graph_positions.json"


def generate() -> dict:
    graph_data = json.loads(GRAPH_DATA.read_text(encoding="utf-8"))
    node_ids = sorted(n["id"] for n in graph_data["nodes"])
    n = len(node_ids)

    center = [0.5, 0.5]
    scale = 1.0

    positions = {}
    for i, node_id in enumerate(node_ids):
        angle = 2 * math.pi * i / n
        nx = 0.5 + 0.5 * math.cos(angle)
        ny = 0.5 + 0.5 * math.sin(angle)
        positions[node_id] = {"nx": nx, "ny": ny, "fixed": True}

    return {
        "_комментарий": "Детерминированная круговая раскладка графа. "
        "Генерируется scripts/build_graph_positions.py из graph_data.json. "
        "Ручная правка запрещена.",
        "_источники": ["docs/graph_data.json"],
        "layouts": {
            "graph": {
                "center": center,
                "scale": scale,
                "count": n,
                "positions": positions,
            }
        },
    }


def main(check: bool = False) -> int:
    generated = generate()
    if check:
        current = json.loads(OUT.read_text(encoding="utf-8"))
        if current != generated:
            print("[!] graph_positions.json differs from generated (--check failed)")
            return 1
        print(f"[OK] graph_positions.json matches generated ({generated['layouts']['graph']['count']} positions)")
        return 0

    text = json.dumps(generated, ensure_ascii=False, indent=2) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"[OK] wrote {OUT}: {generated['layouts']['graph']['count']} positions")
    return 0


if __name__ == "__main__":
    import sys

    check = "--check" in sys.argv[1:]
    raise SystemExit(main(check=check))
