"""Скачивает pmcid для всех papers через NCBI eutils esummary.

API: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
Возвращает <ArticleId IdType="pmc">PMC1234567</ArticleId> для каждого pmid.

Выход:
  data/papers/pmcids.json  →  {pmid: "PMC1234567", ...}
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "papers" / "pmcids.json"

API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EMAIL = os.environ.get("NCBI_EMAIL", "deadsno@example.com")  # ← поменяй на свой
API_KEY = os.environ.get("NCBI_API_KEY", "")

BATCH = 200
DELAY = 0.34 if not API_KEY else 0.11

HEADERS = {
    "User-Agent": "brain-25-evidence/1.0 (mailto:deadsno@example.com)",
}


def fetch_batch(pmids: list[str]) -> dict[str, str]:
    """Возвращает {pmid: pmcid} для переданных id."""
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "brain-25-evidence",
        "email": EMAIL,
    }
    if API_KEY:
        params["api_key"] = API_KEY

    r = requests.get(API, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()

    out: dict[str, str] = {}
    root = ET.fromstring(r.text)
    for docsum in root.findall(".//DocSum"):
        pmid = docsum.findtext("Id")
        if not pmid:
            continue
        for item in docsum.findall("Item"):
            if item.get("Name") == "ArticleIds":
                for aid in item.findall("Item"):
                    if aid.get("Name") == "pmc":
                        pmcid = (aid.text or "").strip()
                        if pmcid:
                            out[pmid] = pmcid
                        break
    return out


def main() -> int:
    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    pmids = [p for p in papers.keys() if p.isdigit()]
    print(f"Всего PMIDs: {len(pmids)}")

    out: dict[str, str] = {}
    if OUT.exists():
        out = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"Уже скачано: {len(out)}")

    todo = [p for p in pmids if p not in out]
    print(f"Осталось:   {len(todo)}")
    print()

    if not todo:
        print("[OK] Всё уже скачано")
        return 0

    t0 = time.time()
    consec_errors = 0

    for i in range(0, len(todo), BATCH):
        chunk = todo[i : i + BATCH]
        try:
            batch_out = fetch_batch(chunk)
            out.update(batch_out)
            consec_errors = 0
        except Exception as e:
            consec_errors += 1
            print(f"  [ERR {consec_errors}] {i}: {e}")
            if consec_errors >= 3:
                print("  3 ошибки подряд — пауза 30 сек")
                time.sleep(30)
                consec_errors = 0
            continue

        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        done = min(i + BATCH, len(todo))
        rate = done / (time.time() - t0) if time.time() > t0 else 0
        eta = (len(todo) - done) / rate / 60 if rate else 0
        print(f"[{done}/{len(todo)}] pmcid={len(out)} · {rate:.0f} pmid/s · ETA {eta:.1f} мин")
        time.sleep(DELAY)

    print(f"\n[OK] {OUT} — {len(out)} pmcid")
    return 0


if __name__ == "__main__":
    sys.exit(main())