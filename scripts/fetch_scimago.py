"""A3.4.1: SCImago Journal Rank — метаданные журналов.

SCImago отдаёт полный CSV только через ?out=xls (не ?out=csv — вернёт HTML).
Разделитель ';'. Два столбца Publisher (6 и 23) — берём первый.

Выход:
  data/journals/scimago.json — {by_issn: {...}, by_title: {...}}

Использование:
    python scripts\\fetch_scimago.py
    python scripts\\fetch_scimago.py --reset
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    print("[ERROR] curl_cffi не установлен. pip install curl_cffi", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "journals"
OUT = OUT_DIR / "scimago.json"
PAPERS = ROOT / "data" / "papers" / "papers.json"

URL = "https://www.scimagojr.com/journalrank.php?out=xls"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.scimagojr.com/journalrank.php",
}

# Индексы колонок в CSV (0-based). Проверено на scimagojr 2025.csv
COL_RANK = 0
COL_SOURCEID = 1
COL_TITLE = 2
COL_TYPE = 3
COL_ISSN = 4
COL_PUBLISHER = 5          # первый Publisher
COL_SJR = 8
COL_QUARTILE = 9
COL_H_INDEX = 10
COL_COUNTRY = 20
COL_REGION = 21
# 22 = Publisher (дубликат, игнорируем)
COL_COVERAGE = 23
COL_CATEGORIES = 24
COL_AREAS = 25


def download() -> str:
    print(f"  GET {URL}")
    session = curl_requests.Session(impersonate="chrome")
    session.headers.update(HEADERS)
    r = session.get(URL, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    if len(r.content) < 100_000:
        raise RuntimeError(f"Слишком маленький ответ: {len(r.content)} байт")
    return r.text


def parse_sjr(raw: str) -> float | None:
    """'106,094' → 106.094"""
    if not raw:
        return None
    try:
        return float(raw.replace(",", ".").strip())
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUT.exists() and not args.reset:
        print(f"[OK] {OUT} уже существует ({OUT.stat().st_size / 1024:.0f} KB)")
        return 0

    print("Скачиваю SCImago...")
    text = download()
    print(f"  получено {len(text):,} символов")

    by_issn: dict = {}
    by_title: dict = {}
    n = 0
    skipped = 0

    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader, None)
    if not header:
        print("[ERROR] Пустой CSV", file=sys.stderr)
        return 1
    print(f"  колонок: {len(header)}")
    print(f"  header[8]={header[COL_SJR]!r} header[9]={header[COL_QUARTILE]!r}")

    for row in reader:
        if len(row) < 26:
            skipped += 1
            continue
        n += 1
        issn_raw = row[COL_ISSN].strip()
        title = row[COL_TITLE].strip()
        record = {
            "title": title,
            "type": row[COL_TYPE].strip(),
            "sjr": parse_sjr(row[COL_SJR]),
            "quartile": row[COL_QUARTILE].strip(),
            "h_index": row[COL_H_INDEX].strip(),
            "country": row[COL_COUNTRY].strip(),
            "region": row[COL_REGION].strip(),
            "publisher": row[COL_PUBLISHER].strip(),
            "coverage": row[COL_COVERAGE].strip(),
            "categories": row[COL_CATEGORIES].strip(),
            "areas": row[COL_AREAS].strip(),
        }
        # ISSN может быть "15424863, 00079235" — берём первый
        if issn_raw:
            first_issn = issn_raw.split(",")[0].strip()
            if first_issn:
                by_issn[first_issn] = record
        if title:
            by_title[title.lower()] = record

    OUT.write_text(
        json.dumps({
            "by_issn": by_issn,
            "by_title": by_title,
            "_meta": {"total": n, "skipped": skipped, "source": URL},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[OK] {OUT} — {len(by_issn)} по ISSN, {len(by_title)} по названию")
    print(f"     всего строк: {n}, пропущено: {skipped}")

    if PAPERS.exists():
        papers = json.loads(PAPERS.read_text(encoding="utf-8"))
        journals = {p.get("journal") for p in papers.values() if p.get("journal")}
        matched = sum(1 for j in journals if j.lower() in by_title)
        print(f"     Журналов в papers: {len(journals)}")
        print(f"     Найдено в SCImago: {matched} ({matched / max(len(journals), 1) * 100:.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())