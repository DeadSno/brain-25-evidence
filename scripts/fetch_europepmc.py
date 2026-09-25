"""Скачивает full texts через Europe PMC REST API.

Использует эндпоинт /{PMCID}/fullTextXML для получения JATS XML.
Работает только для статей в открытом подмножестве Europe PMC.

Примеры:
    python scripts/fetch_europepmc.py --limit 20
    python scripts/fetch_europepmc.py --workers 3
"""
from __future__ import annotations

import argparse
import json
import sys
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
PMCIDS = ROOT / "data" / "papers" / "pmcids.json"
OUT_DIR = ROOT / "data" / "pmc"
TEXT_DIR = OUT_DIR / "text"
INDEX = OUT_DIR / "index.json"

EBI_API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
NCBI_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EMAIL = "deadsno1613@gmail.com"
TOOL = "brain-25-evidence"
MIN_SIZE = 500  # минимальный размер XML в байтах

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "brain-25-evidence/1.0 (https://github.com/DeadSno/brain-25-evidence)",
})


def _fetch_ebi(pmcid: str) -> tuple[str | None, str]:
    """EBI Europe PMC. Быстро, но 500 на части PMCID."""
    url = f"{EBI_API}/{pmcid}/fullTextXML"
    params = {"email": EMAIL, "tool": TOOL}
    try:
        r = SESSION.get(url, params=params, timeout=30)
    except requests.RequestException as e:
        return None, f"ebi_{type(e).__name__}"

    if r.status_code == 200:
        xml = r.text.strip()
        if len(xml) < MIN_SIZE:
            return None, "ebi_too_small"
        return xml, ""
    return None, f"ebi_http_{r.status_code}"


def _fetch_ncbi(pmcid: str) -> tuple[str | None, str]:
    """NCBI efetch — fallback, работает там где EBI 500."""
    num = pmcid.replace("PMC", "")
    params = {
        "db": "pmc",
        "id": num,
        "rettype": "xml",
        "retmode": "xml",
        "email": EMAIL,
        "tool": TOOL,
    }
    try:
        r = SESSION.get(NCBI_API, params=params, timeout=30)
    except requests.RequestException as e:
        return None, f"ncbi_{type(e).__name__}"

    if r.status_code != 200:
        return None, f"ncbi_http_{r.status_code}"

    xml = r.text.strip()
    if len(xml) < MIN_SIZE:
        return None, "ncbi_too_small"
    if "<ERROR>" in xml[:2000] or "cannot be found" in xml[:2000]:
        return None, "ncbi_not_in_oa"
    return xml, ""


def fetch_fulltext(pmcid: str) -> tuple[str | None, str]:
    """Каскад: EBI → NCBI. Нормализация PMCID от NBSP/zero-width."""
    pmcid = (pmcid.strip()
             .replace("\u00a0", "")
             .replace("\u200b", "")
             .replace("\ufeff", ""))

    xml, err_ebi = _fetch_ebi(pmcid)
    if xml:
        return xml, ""

    time.sleep(random.uniform(0.3, 0.6))
    xml, err_ncbi = _fetch_ncbi(pmcid)
    if xml:
        return xml, ""

    return None, f"{err_ebi}|{err_ncbi}"


def process_one(pmid: str, pmcid: str) -> dict:
    """Скачивает XML и сохраняет в TEXT_DIR как .xml."""
    xml_path = TEXT_DIR / f"{pmid}.xml"
    if xml_path.exists() and xml_path.stat().st_size > MIN_SIZE:
        return {"status": "ok", "type": "europepmc", "source": "cached"}

    xml, err = fetch_fulltext(pmcid)
    if not xml:
        return {"status": "failed", "error": err, "type": "europepmc"}

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml, encoding="utf-8")
    return {"status": "ok", "type": "europepmc", "chars": len(xml)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3, help="Потоков (2-5)")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    pmcids = json.loads(PMCIDS.read_text(encoding="utf-8"))
    index: dict = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}

    tasks: list[tuple[str, str]] = []
    for pmid in papers:
        pmcid_full = pmcids.get(pmid)
        if not pmcid_full:
            continue
        pmcid = pmcid_full.strip()  # оставляем "PMC1234567" как есть
        if not pmcid.upper().startswith("PMC"):
            continue
        rec = index.get(pmid, {})
        if rec.get("status") == "ok":
            continue
        # Failed'ы пересматриваются через каскад
        tasks.append((pmid, pmcid))

    if args.limit:
        tasks = tasks[: args.limit]

    print(f"К обработке (Europe PMC): {len(tasks)}")
    print(f"Потоков:                  {args.workers}")
    print()

    if not tasks:
        print("[OK] Нет задач")
        return 0

    t0 = time.time()
    done = ok = err = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_one, pmid, pmcid): pmid
                   for pmid, pmcid in tasks}
        for fut in as_completed(futures):
            pmid = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": "failed", "error": str(e), "type": "europepmc"}

            index[pmid] = result
            done += 1
            if result.get("status") == "ok":
                ok += 1
            else:
                err += 1
                print(f"  [FAIL] {pmid}: {result.get('error')}")

            if done % 20 == 0:
                INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(tasks) - done) / rate / 60 if rate else 0
                print(f"[{done}/{len(tasks)}] ok={ok} err={err} · "
                      f"{rate:.1f} files/s · ETA {eta:.1f} мин")

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(f"\n[OK] ok={ok}, err={err}, время {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())