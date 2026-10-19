"""Заполнение пустых 'citations' через data/journals/nlm_catalog.json (офлайн)
и формирование reports/NULL_EVIDENCE.md для null hedges_g / hedges_g_ci.

- citations: для записи с пустым citations берём первый PMID из key_sources,
  ищем журнал в nlm_catalog (by_title) и составляем citation-строку.
- NULL_EVIDENCE.md: каждая запись с null hedges_g (нет мета-анализа в
  papers_slim — там нет полей effect_size/ci_low/ci_high) фиксируется с
  id + причиной.
"""
import json
from pathlib import Path

DATA_PATH = Path("docs/data.json")
NLM_PATH = Path("data/journals/nlm_catalog.json")
REPORT_PATH = Path("reports/NULL_EVIDENCE.md")


def citation_string(ks0, nlm_by_title):
    """Собирает citation-строку из первого key_sources + nlm_catalog."""
    pmid = ks0.get("pmid")
    journal = ks0.get("journal", "")
    year = ks0.get("year")
    title = ks0.get("title", "")
    entry = nlm_by_title.get(journal.strip().lower(), {}) if journal else {}
    nlmid = entry.get("nlmid", "")
    canon_title = entry.get("title", journal)
    parts = [canon_title]
    if year:
        parts.append(str(year))
    if pmid:
        parts.append(f"PMID:{pmid}")
    if nlmid:
        parts.append(f"NLMID:{nlmid}")
    return " — ".join(parts)


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    nlm = json.loads(NLM_PATH.read_text(encoding="utf-8"))
    nlm_by_title = nlm.get("by_title", {})

    filled_citations = 0
    for rec in data:
        if rec.get("citations") not in (None, ""):
            continue
        ks = rec.get("key_sources") or []
        if not ks:
            continue
        rec["citations"] = citation_string(ks[0], nlm_by_title)
        filled_citations += 1

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # NULL_EVIDENCE.md — null hedges_g (нет мета-анализа в papers_slim)
    null_hg = [r for r in data if r.get("hedges_g") in (None, "")]
    null_ci = [r for r in data if r.get("hedges_g_ci") in (None, "")]

    lines = [
        "# NULL evidence (hedges_g / hedges_g_ci)",
        "",
        "Записи, для которых не удалось заполнить `hedges_g` / `hedges_g_ci`:",
        "причина — в `data/papers/papers_slim.json` нет мета-анализа для данной "
        "добавки (поля `effect_size`, `ci_low`, `ci_high` отсутствуют).",
        "",
        f"Всего записей с null `hedges_g`: {len(null_hg)}",
        f"Всего записей с null `hedges_g_ci`: {len(null_ci)}",
        "",
        "## hedges_g = null (нет мета-анализа в papers_slim)",
        "",
    ]
    for r in null_hg:
        lines.append(f"- `{r.get('id')}` — нет мета-анализа в papers_slim")
    lines += [
        "",
        "## hedges_g_ci = null (нет мета-анализа в papers_slim)",
        "",
    ]
    for r in null_ci:
        lines.append(f"- `{r.get('id')}` — нет мета-анализа в papers_slim")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"filled citations: {filled_citations}")
    print(f"null hedges_g: {len(null_hg)} -> reports/NULL_EVIDENCE.md")
    print(f"null hedges_g_ci: {len(null_ci)}")


if __name__ == "__main__":
    main()
