"""Синхронизирует pubmed_term в _drafts.json с data_pubmed_terms.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "docs" / "_drafts.json"
TERMS = ROOT / "docs" / "data_pubmed_terms.json"


def main() -> int:
    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
    terms = json.loads(TERMS.read_text(encoding="utf-8"))

    updated = 0
    for c in drafts:
        name = c["id"]
        if name in terms:
            old = c.get("pubmed_term")
            new = terms[name]
            if old != new:
                c["pubmed_term"] = new
                print(f"  {name}")
                print(f"    было: {old}")
                print(f"    стало: {new}")
                updated += 1

    if updated:
        DRAFTS.write_text(json.dumps(drafts, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print(f"\n[OK] Обновлено: {updated} черновиков")
    else:
        print("[OK] Все синхронизированы")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())