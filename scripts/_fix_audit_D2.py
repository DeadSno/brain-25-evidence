"""D2 аудита v2 — замена устаревших PMIDs на свежие (10 карточек).

Стратегия A: старые удаляем, свежие добавляем.
Метаданные новых PMIDs подтягиваются через PubMed esummary (не вбиваются руками).
"""
from __future__ import annotations

import json
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAILTO = "brain25-evidence@users.noreply.github.com"

PATCHES = {
    "Гуперзин А": {
        "remove": ["18425924", "19370686", "23235666"],
        "add": ["39239652", "34924395"],
    },
    "Пикногенол": {
        "remove": ["22513958", "31585179"],
        "add": ["39987124", "37908749"],
    },
    "Валериана": {
        "remove": ["17054208", "20347389", "17517355"],
        "add": ["38359657", "37527850"],
    },
    "Зверобой": {
        "remove": ["28064110"],
        "add": ["36226689", "32478963"],
    },
    "Глюкозамин + хондроитин": {
        "remove": ["15846645", "29713967"],
        "add": ["40647198", "35024906"],
    },
    "Мака": {
        "remove": ["20691074", "21840656"],
        "add": ["36110519", "39796542"],
    },
    "Пажитник": {
        "remove": ["24438170"],
        "add": ["36837450", "36470549"],
    },
    "Кордицепс": {
        "remove": ["25519252", "26457607", "28137532"],
        "add": ["38484953", "39460586"],
    },
    "Рейши": {
        "remove": ["27045603", "22696372"],
        "add": ["36995543", "42147328"],
    },
    "Глутамин": {
        "remove": ["25199493", "11687112"],
        "add": ["39397201", "37882375"],
    },
}


def _get(url, retries=3):
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
    raise RuntimeError(url)


def fetch_meta(pmids):
    """esummary → {pmid: {title, year, journal, pubtype}}."""
    if not pmids:
        return {}
    url = (f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(pmids)}"
           f"&retmode=json&email={urllib.parse.quote(MAILTO)}")
    res = json.loads(_get(url)).get("result", {})
    out = {}
    for p in pmids:
        info = res.get(p, {})
        out[p] = {
            "pmid": p,
            "title": info.get("title", "?"),
            "year": int((info.get("pubdate") or "0")[:4] or 0),
            "journal": info.get("fulljournalname", "?"),
            "pubtype": info.get("pubtype", []) or ["Journal Article"],
            "source": "curated",
        }
    return out


d = json.loads(DATA.read_text(encoding="utf-8"))
by_id = {c["id"]: c for c in d}

# Собираем все новые PMIDs для батч-запроса
all_new = []
for patch in PATCHES.values():
    all_new.extend(patch["add"])
all_new = sorted(set(all_new))

print(f"Загружаю метаданные {len(all_new)} новых PMIDs…")
new_meta = fetch_meta(all_new)
print(f"[OK] Получено {len(new_meta)}\n")

for cid, patch in PATCHES.items():
    c = by_id.get(cid)
    if not c:
        print(f"❌ {cid} не найдена")
        continue

    ks = c.get("key_sources") or []
    before = [str(k.get("pmid")) for k in ks]

    # Удаляем старые
    ks_new = [k for k in ks if str(k.get("pmid")) not in patch["remove"]]

    # Добавляем новые
    for p in patch["add"]:
        if p in new_meta:
            ks_new.append(new_meta[p])
        else:
            print(f"  ⚠️ {cid}: нет метаданных для PMID {p}")

    c["key_sources"] = ks_new
    after = [str(k.get("pmid")) for k in ks_new]

    print(f"=== {cid} ===")
    print(f"  было:  {before}")
    print(f"  стало: {after}")
    print()

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = DATA.with_suffix(f".json.bak-{ts}")
shutil.copy2(DATA, backup)
DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"[OK] Бэкап: {backup.name}")
print(f"[OK] Записано: {DATA}")