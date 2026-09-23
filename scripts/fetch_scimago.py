"""A3.4.1: SCImago Journal Rank — метаданные журналов.

Скачивает публичный SCImago CSV, фильтрует журналы из papers.json.

Выход:
  data/journals/scimago.json — {issn_or_name: {sjr, quartile, h_index, country, publisher}}

Использование:
    python scripts\\fetch_scimago.py
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "journals"
OUT = OUT_DIR / "scimago.json"
PAPERS = ROOT / "data" / "papers" / "papers.json"

URL = "https://www.scimagojr.com/journalrank.php?out=xls"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def download() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


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
    print(f"  получено {len(text)} символов")

    # Парсим CSV (реально это ; или , разделитель — пробуем оба)
    # Первая строка — заголовок
    lines = text.splitlines()
    if not lines:
        print("[ERROR] Пустой CSV", file=sys.stderr)
        return 1

    # Определяем разделитель
    header = lines[0]
    delim = ";" if ";" in header else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    by_issn = {}
    by_title = {}
    n = 0

    for row in reader:
        n += 1
        issn = (row.get("Issn") or "").strip()
        title = (row.get("Title") or "").strip()
        record = {
            "title": title,
            "sjr": row.get("SJR"),
            "quartile": row.get("SJR Best Quartile"),
            "h_index": row.get("H index"),
            "country": row.get("Country"),
            "publisher": row.get("Publisher"),
            "issn": issn,
            "type": row.get("Type"),
            "year": row.get("Year"),
            "citations_per_doc": row.get("Citations / Doc. (2years)"),
        }
        if issn:
            by_issn[issn] = record
        if title:
            by_title[title.lower()] = record

    OUT.write_text(json.dumps({
        "by_issn": by_issn,
        "by_title": by_title,
        "_meta": {"total": n, "source": URL},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {OUT} — {len(by_issn)} по ISSN, {len(by_title)} по названию")

    # Теперь — какие журналы из papers есть в SCImago
    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    journals = {p.get("journal") for p in papers.values() if p.get("journal")}
    matched = sum(1 for j in journals if j.lower() in by_title)
    print(f"     Журналов в papers: {len(journals)}")
    print(f"     Найдено в SCImago: {matched} ({matched/len(journals)*100:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())