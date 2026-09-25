# -*- coding: utf-8 -*-
"""Генерирует reports/q14_batch_16.md из reports/q14_batch_16_proposal.json."""
import json

SRC = "reports/q14_batch_16_proposal.json"
OUT = "reports/q14_batch_16.md"

GRADE_WORDS = {"A": "сильная", "B": "умеренная", "C": "слабая", "D": "доказательств нет"}

def main():
    cards = json.load(open(SRC, encoding="utf-8"))
    lines = []
    lines.append("# Q1.4 batch 16 — обоснование 10 карточек")
    lines.append("")
    lines.append("Бриф: `docs/briefs/q14_batch_16.md` → итог `reports/q14_batch_16_proposal.json`.")
    lines.append("Правила: только abstracts, ничего не выдумано; verdict/grade по шкале; механики [механизм, эффект, сила].")
    lines.append("")
    lines.append("## Сводка")
    lines.append("")
    lines.append("| Добавка | Вердикт | Грейд | Источники |")
    lines.append("|---------|---------|-------|-----------|")
    for name, c in cards.items():
        srcs = ", ".join(f"[{s['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{s['pmid']}/)" for s in c["key_sources"])
        lines.append(f"| {name} | {c['verdict']} | {c['grade']} | {srcs} |")
    lines.append("")

    for name, c in cards.items():
        lines.append(f"## {name} | {c['verdict']} | grade {c['grade']}")
        lines.append("")
        lines.append(f"- **about**: {c['about']}")
        if c.get("who_needs"):
            lines.append(f"- **who_needs**: {c['who_needs']}")
        if c.get("onset"):
            lines.append(f"- **onset**: {c['onset']}")
        if c.get("myths"):
            lines.append(f"- **myths**: {c['myths']}")
        if c.get("food_sources"):
            lines.append(f"- **food_sources**: {c['food_sources']}")
        if c.get("guidelines"):
            lines.append(f"- **guidelines**: {c['guidelines']}")
        if c.get("how_to_choose"):
            lines.append(f"- **how_to_choose**: {c['how_to_choose']}")
        lines.append(f"- **dosage**: {c.get('dosage', '—')}")
        lines.append(f"- **course**: {c.get('course', '—')}")
        lines.append(f"- **caution**: {c.get('caution', '—')}")
        lines.append(f"- **upper_limit**: {c.get('upper_limit', '—')}")
        lines.append("")
        lines.append("### Механизмы")
        lines.append("")
        for m in c["mechs"]:
            lines.append(f"1. **{m[0]}** — `{m[2]}`: {m[1]}")
        lines.append("")
        lines.append("### Эффекты")
        lines.append("")
        lines.append(", ".join(c["effects"]))
        lines.append("")
        lines.append("### Источники (PMID → поле)")
        lines.append("")
        for s in c["key_sources"]:
            j = s.get("journal", "")
            doi = f" doi:{s['doi']}" if s.get("doi") else ""
            lines.append(f"- [{s['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{s['pmid']}/) — {s.get('year', '')} — {j}{doi} — «{s.get('title', '')}»")
        lines.append("")
        lines.append("### Взаимодействия")
        lines.append("")
        for it in c["interactions"]:
            lines.append(f"- `{it['with']}` / {it['severity']}: {it.get('note', '')}")
        lines.append("")
        lines.append("### Обоснование грейда")
        lines.append("")
        reason = _grade_reason(c)
        lines.append(reason)
        lines.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print(f"OK: {OUT} ({len(cards)} карточек)")


def _grade_reason(c):
    w = GRADE_WORDS.get(c["grade"], c["grade"])
    verdict = c["verdict"]
    lines = [
        f"Грейд {c['grade']} («{w} уверенность»), вердикт «{verdict}»."
    ]
    if c["grade"] == "D":
        lines.append("Прямых мета-анализов с назначением добавки людям в подборке нет, эффект в abstracts не показан — честно «не подтверждено».")
    elif c["grade"] == "C":
        lines.append("Эффект описан только в определённом контексте (конкретные пациенты/дефицит), у здоровых не воспроизводится — «зависит от контекста».")
    elif c["grade"] == "B":
        lines.append("Есть мета-анализы с воспроизводимым эффектом в своей группе, но с оговорками по дозе/популяции.")
    elif c["grade"] == "A":
        lines.append("Устойчивый эффект у здоровых по мета-анализам.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
