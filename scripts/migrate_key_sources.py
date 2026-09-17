"""v2.7.1: миграция key_sources из list[str] в единый list[dict].

Старые карточки хранили key_sources как список PMID-строк:
    ["42027564", "39070254", ...]
Новый единый формат (после apply_sources.py) — список словарей:
    [{"pmid": "...", "title": "...", "year": 2024, "journal": "...", "pubtype": [...], "source": "curated"}]

План:
1. Собрать все PMID из карточек, где первый элемент key_sources — строка.
2. Получить метаданные через esummary пачками по 50 (регламент PubMed: <=3 req/s).
3. Переписать данные в dict-формат, сохраняя порядок PMID внутри карточки.
4. Если esummary не вернул PMID (не найден/удалён) — честная пометка, без выдумок
   (validate_sources.py потом пометит его как [MISSING]).

Запуск:
    python scripts/migrate_key_sources.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "brain-25-evidence/1.0"
BATCH = 50
SLEEP = 0.4
RETRIES = 3


def _get(url: str, retries: int = RETRIES) -> str:
    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Failed: {url} ({last_exc})")


def _safe_year(pubdate: str | None) -> int:
    if not pubdate:
        return 0
    head = str(pubdate)[:4]
    return int(head) if head.isdigit() else 0


def esummary(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    raw = _get(url)
    data = json.loads(raw).get("result", {}) or {}
    out: dict[str, dict] = {}
    for pmid in pmids:
        info = data.get(pmid)
        if not isinstance(info, dict) or info.get("error"):
            continue
        out[pmid] = {
            "title": info.get("title") or "?",
            "year": _safe_year(info.get("pubdate")),
            "journal": info.get("fulljournalname") or "?",
            "pubtype": list(info.get("pubtype") or []),
        }
    return out


def make_entry(pmid: str, meta: dict | None) -> dict:
    """dict-запись key_sources. meta=None = PMID не найден в PubMed (честно)."""
    if not meta:
        return {
            "pmid": pmid,
            "title": "(PMID не найден в PubMed)",
            "year": 0,
            "journal": "?",
            "pubtype": [],
            "source": "curated",
        }
    return {
        "pmid": pmid,
        "title": meta["title"],
        "year": meta["year"],
        "journal": meta["journal"],
        "pubtype": meta["pubtype"],
        "source": "curated",
    }


def main() -> int:
    if not DATA_JSON.exists():
        print(f"[!] нет {DATA_JSON}", file=sys.stderr)
        return 1

    raw = DATA_JSON.read_text(encoding="utf-8")
    trailing_nl = raw.endswith("\n")
    data = json.loads(raw)

    legacy = [
        c for c in data
        if isinstance(c.get("key_sources"), list)
        and c["key_sources"]
        and isinstance(c["key_sources"][0], str)
    ]
    if not legacy:
        print("[OK] Устаревших list[str] карточек нет — мигрировать нечего.")
        return 0

    all_pmids: list[str] = []
    seen: set[str] = set()
    for c in legacy:
        for pid in c["key_sources"]:
            if pid not in seen:
                seen.add(pid)
                all_pmids.append(pid)

    print(f"Карточек на миграцию: {len(legacy)} | PMID: {len(all_pmids)}")

    meta_map: dict[str, dict] = {}
    for i in range(0, len(all_pmids), BATCH):
        chunk = all_pmids[i:i + BATCH]
        try:
            meta_map.update(esummary(chunk))
        except Exception as e:  # noqa: BLE001
            print(f"  [!] ошибка esummary пачки {i}-{i + len(chunk)}: {e}",
                  file=sys.stderr)
            return 1
        print(f"  esummary: {i + len(chunk)}/{len(all_pmids)}")
        time.sleep(SLEEP)

    missing = [p for p in all_pmids if p not in meta_map]
    if missing:
        print(f"  [!] PMID не найдены в PubMed: {len(missing)} — "
              f"останутся с честной пометкой (первый: {missing[0]})")

    migrated = 0
    for c in legacy:
        new_ks = [make_entry(pid, meta_map.get(pid)) for pid in c["key_sources"]]
        c["key_sources"] = new_ks
        migrated += 1

    out_text = json.dumps(data, ensure_ascii=False, indent=2)
    if trailing_nl:
        out_text += "\n"
    DATA_JSON.write_text(out_text, encoding="utf-8")

    print(f"[OK] Мигрировано: {migrated} карточек → docs/data.json")
    print(f"     суммарно PMID в dict-формате: {len(all_pmids)}")
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())