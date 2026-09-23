"""Парсит JATS XML из Europe PMC. Извлекает funding, COI, affiliations.

Вход:  data/pmc/text/*.xml (JATS)
Выход: data/processed/xml_meta.json

Пример:
    python scripts/parse_xml_meta.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEXT_DIR = ROOT / "data" / "pmc" / "text"
PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "processed" / "xml_meta.json"

# Регистронезависимые триггеры для неструктурированного funding
FUNDING_TRIGGERS = re.compile(
    r"(fund(ed|ing)?\s+by|supported\s+by|grant\s+"
    r"|financ(ial|ed)\s+support|this\s+work\s+was\s+support)",
    re.IGNORECASE,
)
COI_TRIGGERS = re.compile(
    r"(conflict\s+of\s+interest|competing\s+interests?|"
    r"declaration\s+of\s+interest|no\s+conflict)",
    re.IGNORECASE,
)


def text_of(el: ET.Element | None) -> str:
    """Весь текст элемента, сжатый в одну строку."""
    if el is None:
        return ""
    return " ".join("".join(el.itertext()).split())


def extract_funding(root: ET.Element) -> dict:
    """Ищет funding-group (структ.) или текст в ack/body."""
    out = {"sources": [], "awards": [], "text": "", "structured": False}

    # 1. Структурированный funding
    for fg in root.iter("funding-group"):
        out["structured"] = True
        for fs in fg.iter("funding-source"):
            src = text_of(fs)
            if src:
                out["sources"].append(src)
        for aid in fg.iter("award-id"):
            award = text_of(aid)
            if award:
                out["awards"].append(award)
        # Иногда весь текст в <funding-statement>
        for stmt in fg.iter("funding-statement"):
            s = text_of(stmt)
            if s:
                out["text"] = s

    # 2. Acknowledg(e)ments — часто там "supported by grant..."
    for ack in root.iter("ack"):
        txt = text_of(ack)
        if txt and FUNDING_TRIGGERS.search(txt):
            if not out["text"]:
                out["text"] = txt
            break

    return out


def extract_coi(root: ET.Element) -> str:
    """Ищет COI: <conflict>, <fn fn-type=conflict>, или из ack."""
    # 1. Явный тег <conflict>
    for conf in root.iter("conflict"):
        t = text_of(conf)
        if t:
            return t[:2000]

    # 2. <fn fn-type="conflict"> или fn-type="COI"
    for fn in root.iter("fn"):
        ftype = (fn.get("fn-type") or "").lower()
        if "conflict" in ftype or "coi" in ftype:
            t = text_of(fn)
            if t:
                return t[:2000]

    # 3. Поиск в <ack>
    for ack in root.iter("ack"):
        t = text_of(ack)
        if t and COI_TRIGGERS.search(t):
            return t[:2000]

    return ""


def extract_affiliations(root: ET.Element) -> list[str]:
    """Все <aff> с affiliation-строками."""
    affs = []
    for aff in root.iter("aff"):
        t = text_of(aff)
        if t:
            affs.append(t[:300])
    return affs


def extract_countries(affs: list[str]) -> list[str]:
    """Грубый парс стран из аффилиаций — по последнему слову."""
    # Список ключевых стран — расширяй по необходимости
    KNOWN = {
        "USA", "UK", "Germany", "France", "Italy", "Spain", "China",
        "Japan", "Korea", "Brazil", "India", "Canada", "Australia",
        "Netherlands", "Sweden", "Switzerland", "Poland", "Turkey",
        "Russia", "Iran", "Israel", "Belgium", "Denmark", "Norway",
        "Finland", "Austria", "Greece", "Portugal", "Mexico", "Egypt",
    }
    found = set()
    for a in affs:
        for c in KNOWN:
            if c in a:
                found.add(c)
    return sorted(found)


def parse_one(path: Path) -> dict | None:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None
    root = tree.getroot()
    pmid = path.stem

    # Метаданные из article-meta
    meta = {
        "pmid": pmid,
        "pmcid": "",
        "doi": "",
        "journal": "",
        "year": "",
        "title": "",
        "has_abstract": False,
        "has_body": False,
    }

    for aid in root.iter("article-id"):
        t = aid.get("pub-id-type")
        if t == "pmcid":
            meta["pmcid"] = (aid.text or "").strip()
        elif t == "doi":
            meta["doi"] = (aid.text or "").strip()

    jt = root.find(".//journal-title")
    if jt is not None:
        meta["journal"] = text_of(jt)

    for pd in root.iter("pub-date"):
        y = pd.find("year")
        if y is not None and y.text:
            meta["year"] = y.text.strip()
            break

    at = root.find(".//article-title")
    if at is not None:
        meta["title"] = text_of(at)[:500]

    if root.find(".//abstract") is not None:
        meta["has_abstract"] = True
    if root.find(".//body") is not None:
        meta["has_body"] = True

    affs = extract_affiliations(root)
    funding = extract_funding(root)
    coi = extract_coi(root)
    countries = extract_countries(affs)

    meta["affiliations"] = affs  # сырые строки для анализа стран
    meta["n_affiliations"] = len(affs)
    meta["countries"] = countries
    meta["funding_sources"] = funding["sources"][:20]
    meta["funding_awards"] = funding["awards"][:20]
    meta["funding_text"] = funding["text"][:1500]
    meta["funding_structured"] = funding["structured"]
    meta["has_funding"] = bool(funding["sources"] or funding["text"])
    meta["coi_text"] = coi[:1500]
    meta["has_coi"] = bool(coi)

    return meta


def main() -> int:
    xml_files = list(TEXT_DIR.glob("*.xml"))
    print(f"XML файлов: {len(xml_files)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}

    parsed = 0
    for i, path in enumerate(xml_files, 1):
        rec = parse_one(path)
        if rec:
            out[rec["pmid"]] = rec
            parsed += 1
        if i % 500 == 0:
            print(f"  [{i}/{len(xml_files)}] parsed={parsed}")
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    # Статистика
    n = len(out)
    with_fund = sum(1 for r in out.values() if r["has_funding"])
    with_coi = sum(1 for r in out.values() if r["has_coi"])
    with_body = sum(1 for r in out.values() if r["has_body"])

    print(f"\n[OK] {OUT}")
    print(f"  Всего:        {n}")
    print(f"  С abstract:   {sum(1 for r in out.values() if r['has_abstract'])}")
    print(f"  С body:       {with_body}")
    print(f"  С funding:    {with_fund} ({with_fund/n*100:.1f}%)")
    print(f"  С COI:        {with_coi} ({with_coi/n*100:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())