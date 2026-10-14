"""Аудит длины SEO-мет: `<title>` 40–60, `meta description` 120–160.

Закрывает базу для SEO-P1-01/02 (`reports/audits/seo.md`): сколько страниц
вне нормы и где именно. Скрипт ТОЛЬКО ЧИТАЕТ и печатает CSV — правкой он
не занимается (правка смысловая, поштучно).

Запуск:
    python scripts/audit_meta_lengths.py                 # основные страницы
    python scripts/audit_meta_lengths.py --include-sup   # + 131 sup/*.html
    python scripts/audit_meta_lengths.py --csv out.csv   # свой путь CSV

Исключения по умолчанию (генератор/служебное, правка — отдельная задача):
    docs/sup/**        — 131 страница, собирается scripts/build_sup.py
    docs/vendor/**     — сторонние библиотеки
    docs/offline.html  — офлайн-обёртка service worker
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

TITLE_MIN, TITLE_MAX = 40, 60
DESC_MIN, DESC_MAX = 120, 160

EXCLUDE_DIRS = {"vendor"}
EXCLUDE_FILES = {"offline.html"}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESC_RE = re.compile(
    r"""<meta[^>]*\bname\s*=\s*["']description["'][^>]*\bcontent\s*=\s*["'](.*?)["']""",
    re.IGNORECASE | re.DOTALL,
)
# обратный порядок атрибутов: content= до name=
DESC_RE_ALT = re.compile(
    r"""<meta[^>]*\bcontent\s*=\s*["'](.*?)["'][^>]*\bname\s*=\s*["']description["']""",
    re.IGNORECASE | re.DOTALL,
)


def clean(raw: str) -> str:
    """Текст меты без тегов и HTML-экранирования."""
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw))).strip()


def excluded(path: Path, include_sup: bool) -> bool:
    rel = path.relative_to(DOCS)
    if rel.parts[0] in EXCLUDE_DIRS:
        return True
    if rel.name in EXCLUDE_FILES:
        return True
    if not include_sup and rel.parts[0] == "sup":
        return True
    return False


def collect(include_sup: bool) -> list[tuple[str, str, int, str]]:
    """-> [(file, field, length, value)]; отсутствующая мета = длина -1."""
    rows: list[tuple[str, str, int, str]] = []
    for path in sorted(DOCS.rglob("*.html")):
        if excluded(path, include_sup):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")

        m = TITLE_RE.search(text)
        title = clean(m.group(1)) if m else ""
        rows.append((rel, "title", len(title) if title else -1, title))

        m = DESC_RE.search(text) or DESC_RE_ALT.search(text)
        desc = clean(m.group(1)) if m else ""
        rows.append((rel, "description", len(desc) if desc else -1, desc))
    return rows


def bucket(length: int, lo: int, hi: int) -> str:
    if length < 0:
        return "ОТСУТСТВУЕТ"
    if length < lo:
        return f"короткий (<{lo})"
    if length > hi:
        return f"длинный (>{hi})"
    return "норма"


def report(rows: list[tuple[str, str, int, str]], field: str, lo: int, hi: int) -> None:
    subset = [r for r in rows if r[1] == field]
    present = [r for r in subset if r[2] >= 0]
    missing = [r for r in subset if r[2] < 0]
    bad = [r for r in present if not (lo <= r[2] <= hi)]

    counts: dict[str, int] = {}
    for r in subset:
        counts[bucket(r[2], lo, hi)] = counts.get(bucket(r[2], lo, hi), 0) + 1

    lens = [r[2] for r in present]
    print(f"\n=== {field} (норма {lo}–{hi}) ===")
    print(f"  страниц с метой: {len(present)} / {len(subset)}   вне нормы: {len(bad)}")
    if lens:
        print(
            f"  длина: медиана {statistics.median(lens):.0f}, "
            f"min {min(lens)}, max {max(lens)}, среднее {statistics.fmean(lens):.1f}"
        )
    for k in sorted(counts, key=lambda x: -counts[x]):
        print(f"    {k:22s} {counts[k]:4d}")
    for rel, _f, length, value in missing:
        print(f"    ОТСУТСТВУЕТ: {rel} ({value!r})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(ROOT / "reports" / "meta_lengths.csv"))
    ap.add_argument("--include-sup", action="store_true", help="не исключать docs/sup/*")
    args = ap.parse_args(argv)

    rows = collect(args.include_sup)
    pages = len({r[0] for r in rows})
    print(f"Просканировано: {pages} страниц, {len(rows)} мет")
    print(f"Исключения: sup/* {'ВКЛЮЧЁН' if args.include_sup else 'исключён'}, "
          f"vendor/*, offline.html")

    report(rows, "title", TITLE_MIN, TITLE_MAX)
    report(rows, "description", DESC_MIN, DESC_MAX)

    csv_path = Path(args.csv)
    csv_path = csv_path if csv_path.is_absolute() else (Path.cwd() / csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "field", "length", "value"])
        w.writerows(rows)
    shown = csv_path.relative_to(ROOT).as_posix() if csv_path.is_relative_to(ROOT) else csv_path
    print(f"\nCSV: {shown}")

    bad_pages = {
        r[0] for r in rows
        if r[2] >= 0 and not (
            (r[1] == "title" and TITLE_MIN <= r[2] <= TITLE_MAX)
            or (r[1] == "description" and DESC_MIN <= r[2] <= DESC_MAX)
        )
    }
    print(f"Страниц вне нормы хотя бы по одному полю: {len(bad_pages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
