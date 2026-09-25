"""Импорт JSON → DuckDB для SQL-анализа.

Читает:
    docs/data.json         — 130 карточек
    data/papers/papers.json — 37 618 papers (опционально)
    reports/coi_report.json — COI для 6 310 papers

Создаёт:
    data/db/brain.duckdb   — аналитическая БД

Запуск:
    python scripts/db/import_to_duckdb.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DATA_JSON = ROOT / "docs" / "data.json"
PAPERS_JSON = ROOT / "data" / "papers" / "papers.json"
COI_JSON = ROOT / "reports" / "coi_report.json"
SCHEMA_SQL = ROOT / "scripts" / "db" / "schema.sql"
DB_PATH = ROOT / "data" / "db" / "brain.duckdb"


def load_schema(con: duckdb.DuckDBPyConnection) -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    con.execute(sql)
    print(f"[OK] Схема загружена из {SCHEMA_SQL.name}")


def import_supplements(con: duckdb.DuckDBPyConnection) -> int:
    cards = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    print(f"Карточек: {len(cards)}")

    # 1. supplement
    supp_rows = []
    for c in cards:
        supp_rows.append({
            "id": c["id"],
            "category_id": c.get("category"),
            "grade": c.get("grade"),
            "verdict": c.get("verdict"),
            "code": c.get("code"),
            "about": c.get("about"),
            "who_needs": c.get("who_needs"),
            "onset": c.get("onset"),
            "myths": c.get("myths"),
            "food_sources": c.get("food_sources"),
            "guidelines": c.get("guidelines"),
            "how_to_choose": c.get("how_to_choose"),
            "dosage": c.get("dosage"),
            "course": c.get("course"),
            "caution": c.get("caution"),
            "upper_limit": c.get("upper_limit"),
            "science_index": c.get("scienceIndex"),
            "rct": c.get("rct"),
            "meta_count": c.get("metaCount"),
            "citations": c.get("citations"),
        })
    con.executemany(
        "INSERT INTO supplement VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [tuple(r.values()) for r in supp_rows],
    )
    print(f"[OK] supplement: {len(supp_rows)}")

    # 2. mech
    mech_rows = []
    for c in cards:
        for m in c.get("mechs", []):
            if not m or len(m) < 3:
                continue
            mech_rows.append((c["id"], m[0], m[1], m[2]))
    if mech_rows:
        rows_with_id = [(i+1,) + r for i, r in enumerate(mech_rows)]
        con.executemany(
            "INSERT INTO mech (id, supplement_id, mechanism, effect, strength) VALUES (?,?,?,?,?)",
            rows_with_id,
        )
    print(f"[OK] mech: {len(mech_rows)}")

    # 3. interaction
    inter_rows = []
    for c in cards:
        for i in c.get("interactions", []):
            w = i.get("with", "")
            inter_rows.append((
                c["id"], w, i.get("severity", "low"), i.get("note", "")
            ))
    if inter_rows:
        rows_with_id = [(i+1,) + r for i, r in enumerate(inter_rows)]
        con.executemany(
            "INSERT INTO interaction (id, supplement_id, with_target, severity, note) VALUES (?,?,?,?,?)",
            rows_with_id,
        )
    print(f"[OK] interaction: {len(inter_rows)}")

    # 4. key_source
    src_rows = []
    for c in cards:
        for s in c.get("key_sources", []):
            src_rows.append((
                c["id"],
                s.get("pmid", ""),
                s.get("doi", ""),
                s.get("title", ""),
                s.get("year"),
                s.get("journal", ""),
            ))
    if src_rows:
        rows_with_id = [(i+1,) + r for i, r in enumerate(src_rows)]
        con.executemany(
            "INSERT INTO key_source (id, supplement_id, pmid, doi, title, year, journal) VALUES (?,?,?,?,?,?,?)",
            rows_with_id,
        )
    print(f"[OK] key_source: {len(src_rows)}")

    # 5. effect_tag + supplement_tag
    tags_data = json.loads((ROOT / "docs" / "effect_tags.json").read_text(encoding="utf-8"))
    unique_tags = set()
    for tags in tags_data.values():
        unique_tags.update(tags)
    if unique_tags:
        con.executemany("INSERT INTO effect_tag (tag) VALUES (?)",
                        [(t,) for t in unique_tags])
        tag_rows = []
        for cid, tags in tags_data.items():
            for t in tags:
                tag_rows.append((cid, t))
        con.executemany(
            "INSERT INTO supplement_tag (supplement_id, tag) VALUES (?,?)",
            tag_rows,
        )
        print(f"[OK] effect_tag: {len(unique_tags)}, supplement_tag: {len(tag_rows)}")

    return len(supp_rows)


def import_papers(con: duckdb.DuckDBPyConnection) -> int:
    if not PAPERS_JSON.exists():
        print("[SKIP] papers.json не найден")
        return 0
    papers = json.loads(PAPERS_JSON.read_text(encoding="utf-8"))
    print(f"Papers в источнике: {len(papers)}")

    rows = []
    if isinstance(papers, dict):
        for pmid, p in papers.items():
            rows.append((
                str(pmid),
                p.get("pmcid"),
                p.get("doi"),
                p.get("title", "")[:1000],
                p.get("year"),
                (p.get("journal") or "")[:200],
                (p.get("abstract") or "")[:5000],
            ))
    if rows:
        con.executemany(
            "INSERT INTO paper (pmid, pmcid, doi, title, year, journal, abstract) VALUES (?,?,?,?,?,?,?)",
            rows,
        )
    print(f"[OK] paper: {len(rows)}")
    return len(rows)


def import_coi(con: duckdb.DuckDBPyConnection) -> int:
    if not COI_JSON.exists():
        print("[SKIP] coi_report.json не найден")
        return 0
    coi = json.loads(COI_JSON.read_text(encoding="utf-8"))
    samples = coi.get("samples", [])

    # samples содержит только 20 примеров, реальных данных нет в отчёте.
    # Для полноценного импорта COI нужен отдельный dump. Пока — заглушка.
    print(f"[INFO] COI: samples {len(samples)} (полные данные не в отчёте)")
    return 0


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    try:
        load_schema(con)
        n_supp = import_supplements(con)
        n_papers = import_papers(con)
        n_coi = import_coi(con)

        # Финальная сводка
        print()
        print("=== Итог ===")
        for t in ("supplement", "mech", "interaction", "key_source",
                  "effect_tag", "supplement_tag", "paper", "coi"):
            try:
                cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t:20} {cnt:>8}")
            except Exception:
                pass
    finally:
        con.close()

    print(f"\n[OK] {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
