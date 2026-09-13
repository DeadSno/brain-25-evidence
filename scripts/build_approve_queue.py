"""v2.4: approves-очередь — кандидаты Hedges' g из PubMed (мета-анализы).
Строит docs/approve_queue.md БЕЗ записи g в data.json: владелец смотрит ряд
и помечает «ок»/«нет» — только после «ок» значение переезжает в docs/data.json.
Ключ к сверке с приорами соавтора: |extract_g − PRIOR_G| ≤ 0.1 → «приор совпал».

Запуск:
    python scripts/build_approve_queue.py [--top10]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.content import PRIOR_G  # noqa: E402
from scripts.extract_g import candidates, year_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
OUT = ROOT / "docs" / "approve_queue.md"

# sid (id в data.json) → PubMed-запрос. Для топ-10 и состава PRIOR_G.
QUERIES = {
    "Креатин": "creatine AND memory",
    "Кофеин": "caffeine AND cognition",
    "Мелатонин": "melatonin AND sleep",
    "Омега-3": "omega-3 fatty acids AND cognition",
    "Витамин D": "vitamin D AND depression",
    "Магний": "magnesium AND anxiety",
    "Куркумин": "curcumin AND depression",
    "Пробиотики": "probiotics AND depression",
    "Цинк": "zinc AND depression",
    "Витамин C": "vitamin C AND immune",
    "Бакопа": "bacopa monnieri AND memory",
    "Ашваганда": "ashwagandha AND stress",
    "Родиола": "rhodiola rosea AND fatigue",
    "L-Теанин": "l-theanine AND anxiety",
    "Гинкго": "ginkgo biloba AND cognition",
    "Коллаген": "collagen AND skin",
    "Берберин": "berberine AND glucose",
    "Имбирь": "ginger AND nausea",
}


def match_prior(sid: str, g: float | None) -> float | None:
    """Приор для sid (по подстроке), если совпадает ±0.1 — возвращает приор,
    иначе None (совпадения нет или приора для sid нет)."""
    for name, prior in PRIOR_G.items():
        if name in sid or sid in name:
            if g is not None and abs(g - prior) <= 0.1:
                return prior
            return None
    return None


def query_outcome(snippet: str) -> str:
    """Первые 40 значимых символов сниппета как «исход»."""
    t = snippet.strip()
    return t[:40].replace("\n", " ") if t else "—"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top10", action="store_true", help="только EDU_TOP10")
    args = ap.parse_args()

    ids = [c["id"] for c in json.loads(DATA.read_text(encoding="utf-8"))]
    chosen = [sid for sid in QUERIES if sid in ids]
    if args.top10:
        top = {"Креатин", "Кофеин", "Мелатонин", "Омега-3", "Витамин D",
               "Магний", "Куркумин", "Пробиотики", "Цинк", "Витамин C"}
        chosen = [c for c in chosen if c in top]

    rows = []
    for sid in chosen:
        for cand in candidates(sid, QUERIES[sid]):
            ci = "—"
            if cand["ci"]:
                ci = f"{cand['ci'][0]:.2f}..{cand['ci'][1]:.2f}"
            g = cand["g"]
            prior = match_prior(sid, g)
            ok = "да" if prior is not None else "?"
            rows.append({
                "sid": sid, "pmid": cand["pmid"], "year": year_of(cand["pmid"]),
                "g": f"{g:+.2f}", "ci": ci, "outcome": query_outcome(cand["snippet"]),
                "snippet": cand["snippet"].replace("\n", " ").replace("|", r"\|")[:120],
                "prior": f"{prior:.2f}" if prior is not None else "—",
                "ok": ok})

    lines = [
        "# APPROVE-ОЧЕРЕДЬ кандидатов Hedges' g (цикл 4)",
        "",
        "> g из абстрактов мета-анализов PubMed (esearch+efetch). В data.json",
        "> НЕ записывается, пока владелец не пометит «ок» в этой таблице.",
        "> |extract_g − PRIOR_G| ≤ 0.1 → колонка «приор совпал» = да.",
        "",
        "| добавка | pmid | год | g | CI | исход | сниппет | приор ±0.1 совпал? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['sid']} | [{r['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/) "
                     f"| {r['year']} | {r['g']} | {r['ci']} | {r['outcome']} | "
                     f"`{r['snippet']}` | {r['ok']} |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"approve_queue.md: {len(rows)} кандидатов по {len(set(r['sid'] for r in rows))} добавкам")


if __name__ == "__main__":
    main()