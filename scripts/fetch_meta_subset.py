import json, time, pathlib, re, requests
import xml.etree.ElementTree as ET
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMM   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OUT = pathlib.Path("data/raw/pubmed"); OUT.mkdir(parents=True, exist_ok=True)
data = json.loads(pathlib.Path("docs/data.json").read_text(encoding="utf-8"))
N_STUD = re.compile(r"\b(\d+)\s+(?:RCT|randomized|randomised|trials|studies)", re.I)
UPD = re.compile(r"\bupdate\b|\bupdated\b", re.I)
target_names = ['SAMe','Йохимбин','Пажитник','Трибулус','Кордицепс','Рейши','Хлорофилл','Сывороточный протеин','Босвеллия','Кверцетин']
done = 0
for s in data:
    if s.get("name") not in target_names:
        continue
    term = s.get("pubmed_term")
    if not term:
        print(f'{s["name"]}: НЕТ pubmed_term'); continue
    syn = [w.strip().lower() for w in re.findall(r"\(([^)]+)\)", term)[0].split(" OR ")]
    q = f'(({term})[tiab]) AND ("meta-analysis"[pt] OR "systematic review"[pt])'
    try:
        r = requests.get(ESEARCH, params={"db":"pubmed","term":q,"retmax":500,"sort":"relevance","retmode":"json"}, timeout=20)
        ids = r.json()["esearchresult"]["idlist"]; time.sleep(0.4)
    except Exception as e:
        print(f'{s["name"]}: SEARCH ERROR {e}'); continue
    if not ids:
        (OUT/f'{s["name"]}_catalog.json').write_text("[]",encoding="utf-8")
        (OUT/f'{s["name"]}.json').write_text("[]",encoding="utf-8")
        print(f'{s["name"]}: 0 МА'); done += 1; continue
    raw = []
    for i in range(0, len(ids), 100):
        try:
            e = requests.get(ESUMM, params={"db":"pubmed","id":",".join(ids[i:i+100]),"retmode":"json"}, timeout=30); time.sleep(0.4)
        except: continue
        for pmid, rec in e.json().get("result", {}).items():
            if pmid in ("uids",): continue
            pubtypes = rec.get("pubtype", []) or []
            authors = rec.get("authors", []) or []
            first = authors[0].get("name","").split(",")[0].strip() if authors else ""
            m = N_STUD.search(rec.get("title",""))
            raw.append({"pmid":pmid, "year":rec.get("pubdate","")[:4],
                        "journal":rec.get("fulljournalname",""),
                        "cochrane":"cochrane" in rec.get("fulljournalname","").lower(),
                        "retracted":"Retracted Publication" in pubtypes,
                        "is_update":bool(UPD.search(rec.get("title",""))),
                        "first_author":first,
                        "n_studies":int(m.group(1)) if m else None, "title":rec.get("title","")})
    identified = len(raw)
    screened = [x for x in raw if any(w in x["title"].lower() for w in syn)]
    after_retract = [x for x in screened if not x["retracted"]]
    seen = {}; deduped = []
    for x in after_retract:
        key = (x["first_author"], x["year"])
        if key not in seen:
            seen[key] = x; deduped.append(x)
        else:
            if int(x["pmid"]) > int(seen[key]["pmid"]):
                deduped = [d for d in deduped if not (d["first_author"]==key[0] and d["year"]==key[1])]
                deduped.append(x); seen[key] = x
    (OUT/f'{s["name"]}_catalog.json').write_text(json.dumps(deduped,ensure_ascii=False,indent=1),encoding="utf-8")
    short = sorted(deduped, key=lambda x: (not x["cochrane"], x["is_update"], -(int(x["year"] or 0)), -(x["n_studies"] or 0)))[:15]
    rows = []
    if short:
        try:
            f = requests.get(EFETCH, params={"db":"pubmed","id":",".join(x["pmid"] for x in short),"rettype":"abstract","retmode":"xml"}, timeout=30); time.sleep(0.4)
            root = ET.fromstring(f.text)
            by_pmid = {art.findtext(".//PMID") or "": art for art in root.iter("PubmedArticle")}
            for x in short:
                art = by_pmid.get(x["pmid"])
                if art is None: continue
                rows.append({"pmid":x["pmid"], "cochrane":x["cochrane"],
                             "title":art.findtext(".//ArticleTitle") or "",
                             "abstract":" ".join(t.text or "" for t in art.iter("AbstractText"))})
        except: pass
    (OUT/f'{s["name"]}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding="utf-8")
    print(f'[{done+1}] {s["name"]}: найдено={identified} скрининг={len(screened)} ретракт={len(screened)-len(after_retract)} дубль={len(after_retract)-len(deduped)} финал={len(deduped)} читано={len(rows)}')
    done += 1
print(f"готово, обработано {done} добавок")
