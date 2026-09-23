"""A3.2.1: PMID → PMCID через elink.

Один batch-запрос на 200 PMIDs. Устойчив к падениям (сохраняет после каждого батча).

Выход:
  data/papers/pmcid_map.json  — {pmid: pmcid | null}

Использование:
    python scripts\\fetch_pmcid.py --limit 2          # тест
    python scripts\\fetch_pmcid.py                    # все 37k
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import MAILTO  # noqa: E402

PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "papers" / "pmcid_map.json"

ELINK = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
RATE_DELAY = 0.34
BATCH = 200


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25-pmcid/1.0 ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def elink_batch(pmids: list[str]) -> dict[str, str | None]:
    """Возвращает {pmid: pmcid | None} для батча."""
    if not pmids:
        return {}
    params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "brain25-pmcid",
        "email": MAILTO,
    }
    url = f"{ELINK}?{urllib.parse.urlencode(params)}"
    try:
        xml_bytes = http_get(url, timeout=90)
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        print(f"    [elink ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return {}

    out: dict[str, str | None] = {p: None for p in pmids}

    # Структура: LinkSet → LinkSetDb (LinkName="pubmed_pmc") → Link → Id
    for linkset in root.findall(".//LinkSet"):
        pmid_el = linkset.find(".//IdList/Id")
        if pmid_el is None:
            continue
        pmid = pmid_el.text.strip() if pmid_el.text else None
        if not pmid:
            continue

        # Ищем ссылку на PMC
        for linksetdb in linkset.findall(".//LinkSetDb"):
            name = linksetdb.findtext("LinkName", "")
            if name == "pubmed_pmc":
                pmc_el = linksetdb.find(".//Link/Id")
                if pmc_el is not None and pmc_el.text:
                    out[pmid] = f"PMC{pmc_el.text.strip()}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Только N батчей (для теста)")
    ap.add_argument("--reset", action="store_true", help="Игнорировать кэш")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    pmids = sorted(papers.keys())
    print(f"Всего PMIDs: {len(pmids)}")

    cache: dict[str, str | None] = {}
    if OUT.exists() and not args.reset:
        cache = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"Кэш: {len(cache)} записей")

    todo = [p for p in pmids if p not in cache]
    print(f"К обработке: {len(todo)}\n")

    if not todo:
        print("[OK] Всё уже обработано")
        return 0

    batches = [todo[i:i+BATCH] for i in range(0, len(todo), BATCH)]
    if args.limit:
        batches = batches[: args.limit]

    t0 = time.time()
    for i, batch in enumerate(batches, 1):
        print(f"[{i}/{len(batches)}] {len(batch)} PMIDs...", end=" ", flush=True)
        result = elink_batch(batch)
        n_oa = sum(1 for v in result.values() if v)
        cache.update(result)
        print(f"PMC найдено: {n_oa}/{len(batch)}")

        # Сохраняем после каждого батча
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        time.sleep(RATE_DELAY)

    n_pmc = sum(1 for v in cache.values() if v)
    print(f"\n[OK] {OUT}")
    print(f"     Всего: {len(cache)}")
    print(f"     С PMCID: {n_pmc} ({n_pmc / len(cache) * 100:.1f}%)")
    print(f"     Время: {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())