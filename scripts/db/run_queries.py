"""Запуск SQL-запросов на DuckDB.

Запросы встроены в скрипт (не парсим .sql — там баги с разделителями).
queries.sql остаётся как документация.

Запуск:
    python scripts/db/run_queries.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "brain.duckdb"

QUERIES = [
    ("Топ-10 добавок по научному индексу", """
        SELECT id, grade, science_index, rct, meta_count
        FROM supplement
        WHERE science_index IS NOT NULL
        ORDER BY science_index DESC
        LIMIT 10
    """),
    ("Распределение по грейдам", """
        SELECT grade, COUNT(*) AS cnt,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM supplement
        GROUP BY grade
        ORDER BY grade
    """),
    ("Категории с наибольшим числом добавок", """
        SELECT category_id, COUNT(*) AS cnt
        FROM supplement
        WHERE category_id IS NOT NULL
        GROUP BY category_id
        ORDER BY cnt DESC
        LIMIT 10
    """),
    ("Взаимодействия по severity", """
        SELECT severity, COUNT(*) AS cnt
        FROM interaction
        GROUP BY severity
        ORDER BY CASE severity
            WHEN 'critical' THEN 1 WHEN 'high' THEN 2
            WHEN 'medium' THEN 3 ELSE 4 END
    """),
    ("Добавки с наибольшим числом механизмов", """
        SELECT s.id, COUNT(m.id) AS mech_count
        FROM supplement s
        JOIN mech m ON m.supplement_id = s.id
        GROUP BY s.id
        ORDER BY mech_count DESC, s.id
        LIMIT 10
    """),
    ("Топ-10 тегов по числу добавок", """
        SELECT tag, COUNT(*) AS cnt
        FROM supplement_tag
        GROUP BY tag
        ORDER BY cnt DESC
        LIMIT 10
    """),
    ("Добавки без key_sources", """
        SELECT s.id, s.grade
        FROM supplement s
        LEFT JOIN key_source ks ON ks.supplement_id = s.id
        WHERE ks.id IS NULL
        ORDER BY s.id
    """),
    ("Лидер категории по scienceIndex (оконная)", """
        WITH ranked AS (
            SELECT category_id, id, science_index,
                ROW_NUMBER() OVER (
                    PARTITION BY category_id
                    ORDER BY science_index DESC NULLS LAST
                ) AS rn
            FROM supplement
            WHERE category_id IS NOT NULL
        )
        SELECT category_id, id, science_index
        FROM ranked
        WHERE rn = 1
        ORDER BY science_index DESC
        LIMIT 15
    """),
    ("Медиана scienceIndex", """
        WITH ranked AS (
            SELECT science_index,
                   ROW_NUMBER() OVER (ORDER BY science_index) AS rn,
                   COUNT(*) OVER () AS cnt
            FROM supplement
            WHERE science_index IS NOT NULL
        )
        SELECT AVG(science_index) AS median_science_index
        FROM ranked
        WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    """),
    ("Papers по годам (тренд)", """
        SELECT year, COUNT(*) AS papers
        FROM paper
        WHERE year BETWEEN 2000 AND 2026
        GROUP BY year
        ORDER BY year
    """),
]


def main() -> int:
    if not DB_PATH.exists():
        print(f"[ERROR] Нет БД: {DB_PATH}")
        print("Сначала: python scripts/db/import_to_duckdb.py")
        return 1

    con = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"Запросов: {len(QUERIES)}\n")

    for i, (title, sql) in enumerate(QUERIES, 1):
        print("=" * 72)
        print(f"  #{i}. {title}")
        print("=" * 72)
        try:
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            print("  " + " | ".join(cols))
            print("  " + "-" * 60)
            for row in rows[:15]:
                print("  " + " | ".join(str(v) for v in row))
            if len(rows) > 15:
                print(f"  ... ({len(rows) - 15} строк пропущено)")
            print(f"  Всего: {len(rows)} строк\n")
        except Exception as e:
            print(f"  [ERROR] {e}\n")

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
