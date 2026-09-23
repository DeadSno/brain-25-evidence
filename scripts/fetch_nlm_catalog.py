"""A3.5.6: NLM Catalog (J_Medline.txt) — маппинг аббревиатур PubMed → полное название.

Скачивает J_Medline.txt, парсит, строит map:
  abbrev_lower → {full_title, issn, nlmid}

Нужен для join_scimago: PubMed даёт 'J Nutr', SCImago — 'The Journal of Nutrition'.

Выход:
  data/journals/nlm_catalog.json

Использование:
    python scripts\\fetch_nlm_catalog.py
    python scripts\\fetch_nlm_catalog.py --reset
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "journals"
OUT = OUT_DIR / "nlm_catalog.json"

URL = "https://ftp.ncbi.nlm.nih.gov/pubmed/J_Medline.txt"
UA = "brain25-evidence/1.0 (https://github.com/DeadSno/brain-25-evidence)"


def download() -> str:
    print(f"  GET {URL}")
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(text: str) -> dict:
    """J_Medline.txt — записи, разделённые '---', поля 'Key: value'.

    Ждём ключи: JournalTitle, MedAbbr, IsoAbbr, ISSN (print), ISSN (online),
    NlmId.
    """
    records = text.split("-" * 3)
    by_abbrev: dict = {}
    by_title: dict = {}
    by_issn: dict = {}
    n = 0

    for rec in records:
        fields: dict = {}
        for line in rec.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip()

        title = fields.get("JournalTitle", "").strip()
        if not title:
            continue
        n += 1

        med_abbr = fields.get("MedAbbr", "").strip().rstrip(".").lower()
        iso_abbr = fields.get("IsoAbbr", "").strip().rstrip(".").lower()
        issn_p = fields.get("ISSN (print)", "").strip()
        issn_e = fields.get("ISSN (online)", "").strip()
        nlmid = fields.get("NlmId", "").strip()

        record = {
            "title": title,
            "issn_print": issn_p,
            "issn_online": issn_e,
            "nlmid": nlmid,
        }

        # Аббревиатуры — ключ для papers
        for abbr in {med_abbr, iso_abbr}:
            if abbr:
                by_abbrev[abbr] = record

        # Полное название — ключ для SCImago
        if title:
            by_title[title.lower()] = record

        # ISSN — fallback
        for issn in {issn_p, issn_e}:
            if issn:
                # SCImago хранит ISSN без дефиса
                by_issn[issn.replace("-", "")] = record

    return {
        "by_abbrev": by_abbrev,
        "by_title": by_title,
        "by_issn": by_issn,
        "_meta": {"total": n, "source": URL},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUT.exists() and not args.reset:
        print(f"[OK] {OUT} уже существует ({OUT.stat().st_size / 1024:.0f} KB)")
        return 0

    print("Скачиваю NLM Catalog...")
    text = download()
    print(f"  получено {len(text):,} символов")

    data = parse(text)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[OK] {OUT}")
    print(f"     Журналов:       {data['_meta']['total']:,}")
    print(f"     Аббревиатур:    {len(data['by_abbrev']):,}")
    print(f"     Полных назв.:   {len(data['by_title']):,}")
    print(f"     ISSN:           {len(data['by_issn']):,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())