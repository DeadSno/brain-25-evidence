"""Фикс Рейши: 36995543 (опечатка) → 36995535 (правильный)."""
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("docs/data.json")
d = json.loads(DATA.read_text(encoding="utf-8"))
c = next(x for x in d if x["id"] == "Рейши")

# Подтягиваем правильные метаданные
url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=36995535&retmode=json"
req = urllib.request.Request(url, headers={"User-Agent": "brain25/1.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    res = json.loads(r.read().decode())["result"]

info = res.get("36995535", {})
correct = {
    "pmid": "36995535",
    "title": info.get("title", "?"),
    "year": int((info.get("pubdate") or "0")[:4] or 0),
    "journal": info.get("fulljournalname", "?"),
    "pubtype": info.get("pubtype", []) or ["Journal Article"],
    "source": "curated",
}
print(f"Правильная статья: {correct['title']}")
print(f"  {correct['year']} · {correct['journal']}\n")

# Заменяем
ks = c.get("key_sources") or []
before = [str(k.get("pmid")) for k in ks]
ks = [k for k in ks if str(k.get("pmid")) != "36995543"]
ks.append(correct)
c["key_sources"] = ks
after = [str(k.get("pmid")) for k in ks]

print(f"было:  {before}")
print(f"стало: {after}")

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = DATA.with_suffix(f".json.bak-{ts}")
shutil.copy2(DATA, backup)
DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\n[OK] Бэкап: {backup.name}")
print(f"[OK] Записано: {DATA}")