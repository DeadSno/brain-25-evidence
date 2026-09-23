# scripts/enrich_species.py
"""Определить species из MeSH-терминов в papers.

Пишет поля:
  species: "human" | "animal" | "both" | "unknown" | "no_mesh"
  species_tags: ["Humans", "Mice", ...]
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"

HUMAN_TAGS = {
    "humans", "adult", "middle aged", "aged", "child", "adolescent",
    "infant", "young adult", "aged, 80 and over", "child, preschool",
    "infant, newborn", "pregnancy", "female", "male",
    # NB: female/male ставятся и животным, но в комбинации с animals
    # их можно отфильтровать — см. логику ниже
}

ANIMAL_TAGS = {
    "animals", "mice", "rats", "rabbits", "dogs", "pigs", "cattle",
    "sheep", "chickens", "zebrafish", "drosophila melanogaster",
    "caenorhabditis elegans", "guinea pigs", "hamsters", "swine",
    "primates", "macaques", "callithrix", "cricetinae", "xenopus",
    "mice, inbred c57bl", "mice, inbred balb c", "mice, knockout",
    "rats, sprague-dawley", "rats, wistar", "bacteria", "fungi",
}

# Human-specific tags (без male/female — они бывают и у животных)
HUMAN_SPECIFIC = HUMAN_TAGS - {"male", "female"}

papers = json.loads(PAPERS.read_text(encoding="utf-8"))
counts = Counter()

for pmid, p in papers.items():
    mesh = p.get("mesh") or []
    mesh_lower = {m.lower().strip() for m in mesh}

    has_human_specific = bool(mesh_lower & HUMAN_SPECIFIC)
    has_animals = bool(mesh_lower & ANIMAL_TAGS)
    has_humans = "humans" in mesh_lower

    if has_humans and has_animals:
        species = "both"
    elif has_humans or has_human_specific:
        species = "human"
    elif has_animals:
        species = "animal"
    elif not mesh_lower:
        species = "no_mesh"
    else:
        species = "unknown"  # не выдумываем in_vitro

    p["species"] = species
    p["species_tags"] = sorted(mesh_lower & (HUMAN_TAGS | ANIMAL_TAGS))
    counts[species] += 1

PAPERS.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"[OK] {PAPERS}")
print(f"     Всего: {len(papers)}")
print(f"\nРаспределение по species:")
total = len(papers)
for s, cnt in counts.most_common():
    print(f"  {s:12s}: {cnt:6d} ({cnt/total*100:.1f}%)")