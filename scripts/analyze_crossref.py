"""Сравнивает funders из CrossRef с Europe PMC XML."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNDERS = ROOT / "data" / "papers" / "funders.json"


def normalize(name: str) -> str:
    name = re.sub(r"https?://\S+", "", name)
    name = re.sub(r"10\.13039/\d+", "", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(".,;:")
    return name


def main() -> int:
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    data = json.loads(FUNDERS.read_text(encoding="utf-8"))
    c = Counter()
    for pmid, rec in data.items():
        if not isinstance(rec, dict):
            continue
        for f in rec.get("funders", []) or []:
            if isinstance(f, str):
                name = f
            elif isinstance(f, dict):
                name = f.get("name", "")
            else:
                continue
            name = normalize(name)
            if 3 < len(name) < 200:
                c[name] += 1

    print(f"=== ТОП-25 FUNDERS (CrossRef, {len(data)} статей) ===")
    for name, n in c.most_common(25):
        print(f"{n:5}  {name[:80]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())