"""Обогащает key_sources DOI через PubMed esummary.

Batch-подход: собирает все уникальные PMID из data.json,
делает 1-2 запроса к esummary (до 200 id за раз),
маппит DOI обратно в key_sources.

Использование:
    python scripts/enrich_dois.py            # dry-run
    python scripts/enrich_dois.py --apply    # записать
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
MAILTO = "brain25-evidence@users.noreply.github.com"


def _get(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": "brain25-evidence/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Failed: {url}")


def fetch_dois(pmids: list[str]) -> dict[str, str]:
    """esummary → {pmid: doi}."""
    if not pmids:
        return {}
    result: dict[str, str] = {}
    # Батчи по 150 (безопасно ниже лимита 200)
    for i in range(0, len(pmids), 150):
        batch = pmids[i:i + 150]
        ids = ",".join(batch)
        url = (f"{EUTILS}?db=pubmed&id={ids}&retmode=json"
               f"&email={urllib.parse.quote(MAILTO)}&tool=brain25_dois")
        raw = _get(url)
        data = json.loads(raw).get("result", {})
        for pmid in batch:
            info = data.get(pmid, {})
            for aid in info.get("articleids", []):
                if aid.get("idtype") == "doi":
                    result[pmid] = aid.get("value", "")
                    break
        time.sleep(0.5)  # rate limit
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    # Собираем все уникальные PMID из key_sources
    all_pmids: set[str] = set()
    for c in data:
        for ks in (c.get("key_sources") or []):
            pmid = str(ks.get("pmid") or "").strip()
            if pmid and re.fullmatch(r"\d+", pmid):
                all_pmids.add(pmid)

    print(f"Уникальных PMID: {len(all_pmids)}")
    print(f"Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    print(f"Запрос esummary (батч)...")
    doi_map = fetch_dois(sorted(all_pmids))
    print(f"  Получено DOI: {len(doi_map)}\n")

    # Считаем изменения
    already_have = 0
    to_add = 0
    missing = 0
    for c in data:
        for ks in (c.get("key_sources") or []):
            pmid = str(ks.get("pmid") or "").strip()
            if ks.get("doi"):
                already_have += 1
                continue
            if doi_map.get(pmid):
                to_add += 1
            else:
                missing += 1

    print(f"key_sources без DOI:")
    print(f"  уже с DOI:    {already_have}")
    print(f"  будет добавлен: {to_add}")
    print(f"  DOI не найден:  {missing}\n")

    # Применяем
    if args.apply:
        added = 0
        for c in data:
            for ks in (c.get("key_sources") or []):
                pmid = str(ks.get("pmid") or "").strip()
                if not ks.get("doi") and doi_map.get(pmid):
                    ks["doi"] = doi_map[pmid]
                    added += 1

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = DATA_JSON.with_suffix(f".json.bak-{ts}")
        shutil.copy2(DATA_JSON, backup)
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Добавлено DOI: {added}")
        print(f"[OK] Бэкап: {backup.name}")
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print("[dry-run] данные не записаны. Добавьте --apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())