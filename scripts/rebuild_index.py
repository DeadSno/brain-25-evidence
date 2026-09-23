"""Восстанавливает data/pmc/index.json из файлов на диске.

Файлы — источник истины. index.json нужен только для skipped-логики
в fetch_* скриптах, чтобы не перекачивать уже скачанное.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_DIR = ROOT / "data" / "pmc" / "text"
INDEX = ROOT / "data" / "pmc" / "index.json"

MIN_SIZE = 500


def main() -> int:
    idx: dict[str, dict] = {}
    for path in TEXT_DIR.iterdir():
        if not path.is_file():
            continue
        pmid = path.stem
        size = path.stat().st_size
        if size < MIN_SIZE:
            continue
        if path.suffix == ".xml":
            typ = "europepmc"
        elif path.suffix == ".txt":
            typ = "pdf_playwright"
        else:
            continue
        idx[pmid] = {
            "status": "ok",
            "type": typ,
            "chars": size,
            "source": "rebuilt_from_disk",
        }

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2),
                     encoding="utf-8")

    n_xml = sum(1 for v in idx.values() if v["type"] == "europepmc")
    n_txt = sum(1 for v in idx.values() if v["type"] == "pdf_playwright")
    print(f"[OK] {INDEX}")
    print(f"  Всего:          {len(idx)}")
    print(f"  europepmc:      {n_xml}")
    print(f"  pdf_playwright: {n_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())