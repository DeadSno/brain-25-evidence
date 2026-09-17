"""Тянет abstracts из PubMed по key_sources карточки для верификации фактов.

Использование:
    python scripts/fetch_evidence.py Креатин
    python scripts/fetch_evidence.py --all      # все 81 карточки

Артефакт: reports/evidence/<safe_id>.md — abstracts + ссылки на PubMed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
OUT_DIR = ROOT / "reports" / "evidence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "brain-25-evidence/1.0 (https://github.com/)"  # NCBI требует UA


def _get(url: str, retries: int = 3) -> str:
    """GET с ретраями на 429/5xx."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Не удалось получить: {url}")


def fetch_abstracts(pmids: list[str]) -> dict[str, dict[str, str]]:
    """efetch → {pmid: {title, abstract, journal, year}}."""
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/efetch.fcgi?db=pubmed&id={ids}&retmode=xml&rettype=abstract"
    xml = _get(url)

    # Разбиваем XML на блоки <PubmedArticle>…</PubmedArticle>
    articles = re.findall(r"<PubmedArticle>.*?</PubmedArticle>", xml, re.DOTALL)

    # Карта: PMID → блок
    by_pmid: dict[str, str] = {}
    for block in articles:
        m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
        if m:
            by_pmid[m.group(1)] = block

    result: dict[str, dict[str, str]] = {}
    for pmid in pmids:
        block = by_pmid.get(pmid)
        if not block:
            result[pmid] = {
                "title": "(PMID не найден в ответе)",
                "abstract": "(не найдено)",
                "journal": "?",
                "year": "?",
            }
            continue

        title_m = re.search(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", block, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "?"

        abs_parts = re.findall(
            r'<AbstractText[^>]*Label="([^"]*)"[^>]*>(.*?)</AbstractText>',
            block, re.DOTALL,
        )
        if not abs_parts:
            raw_parts = re.findall(
                r"<AbstractText[^>]*>(.*?)</AbstractText>", block, re.DOTALL
            )
            abstract = " ".join(
                re.sub(r"<[^>]+>", "", p).strip() for p in raw_parts
            )
        else:
            abstract = " ".join(
                f"[{label}] {re.sub(r'<[^>]+>', '', text).strip()}"
                for label, text in abs_parts
            )

        journal_m = re.search(
            r"<Journal>.*?<Title>(.*?)</Title>", block, re.DOTALL
        )
        journal = re.sub(r"<[^>]+>", "", journal_m.group(1)).strip() if journal_m else "?"

        year_m = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", block, re.DOTALL)
        year = year_m.group(1) if year_m else "?"

        result[pmid] = {
            "title": title,
            "abstract": abstract[:3000] or "(пусто)",
            "journal": journal,
            "year": year,
        }

    return result


def safe_name(name: str) -> str:
    """Имя файла из id: только безопасные символы."""
    return re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE)


def render_card(s: dict, evidence: dict[str, dict[str, str]]) -> str:
    """Markdown-артефакт для ревью одной карточки."""
    lines = [f"# Evidence check: {s['name']} (`{s['id']}`)", ""]
    lines.append(f"- **grade:** `{s.get('grade', '—')}`")
    lines.append(f"- **verdict:** `{s.get('verdict', '—')}`")
    lines.append(f"- **scienceIndex:** {s.get('scienceIndex', '—')} | **metaCount:** {s.get('metaCount', '—')}")
    lines.append(f"- **key_sources:** {len(s.get('key_sources') or [])}")
    lines.append("")

    # Ключевые поля для сверки
    lines.append("## Поля карточки (для сверки с abstracts)")
    lines.append("")
    for f in ["about", "who_needs", "onset", "myths", "food_sources", "guidelines", "how_to_choose"]:
        v = s.get(f) or "_(пусто)_"
        lines.append(f"### `{f}`")
        lines.append(v)
        lines.append("")

    # Abstracts
    lines.append("## Abstracts (PubMed)")
    lines.append("")
    for pmid, info in evidence.items():
        lines.append(f"### PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
        lines.append(f"**{info['title']}** — _{info['journal']}, {info['year']}_")
        lines.append("")
        lines.append(f"> {info['abstract']}")
        lines.append("")

    return "\n".join(lines)


def process_card(s: dict) -> Path:
    """Обрабатывает одну карточку → сохраняет артефакт."""
    pmids = [str(p) for p in (s.get("key_sources") or [])]
    if not pmids:
        content = f"# Evidence check: {s['name']} (`{s['id']}`)\n\n⚠️ **Нет key_sources** — нечего проверять.\n"
        out = OUT_DIR / f"{safe_name(s['id'])}.md"
        out.write_text(content, encoding="utf-8")
        return out

    print(f"  fetching {len(pmids)} PMIDs...")
    evidence = fetch_abstracts(pmids)
    content = render_card(s, evidence)
    out = OUT_DIR / f"{safe_name(s['id'])}.md"
    out.write_text(content, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch PubMed abstracts для верификации")
    parser.add_argument("name", nargs="?", help="ID или name карточки, например «Креатин»")
    parser.add_argument("--all", action="store_true", help="обработать все 81")
    parser.add_argument("--limit", type=int, default=0, help="ограничить N карточками")
    args = parser.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    if args.all:
        cards = data[: args.limit] if args.limit else data
    elif args.name:
        cards = [s for s in data if s["id"] == args.name or s["name"] == args.name]
        if not cards:
            print(f"Карточка «{args.name}» не найдена", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 1

    print(f"Обрабатываю: {len(cards)} карточек → {OUT_DIR}")
    for s in cards:
        print(f"- {s['id']}")
        path = process_card(s)
        print(f"  → {path.name}")
        time.sleep(0.4)  # NCBI: не больше 3 req/sec без ключа
    print(f"\n[OK] Готово. Артефакты: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())