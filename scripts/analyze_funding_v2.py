"""Анализ funders v2 — с нормализацией и каноническими именами.

Вход:  data/processed/xml_meta.json
Выход:
    reports/funding_analysis_v2.txt
    data/processed/funders_top.csv
    data/processed/countries_top.csv
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

# UTF-8 в консоль (Windows)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "data" / "processed" / "xml_meta.json"
OUT_TXT = ROOT / "reports" / "funding_analysis_v2.txt"
OUT_FUND = ROOT / "data" / "processed" / "funders_top.csv"
OUT_CTRY = ROOT / "data" / "processed" / "countries_top.csv"

# Канонический словарь: нижний регистр фрагмент → каноничное имя
CANON = {
    # Китай
    "national natural science foundation of china": "National Natural Science Foundation of China",
    "national key r&d program of china": "National Key R&D Program of China",
    "national key research and development program of china": "National Key R&D Program of China",
    "national basic research program of china": "National Basic Research Program of China",
    "china postdoctoral science foundation": "China Postdoctoral Science Foundation",
    "fundamental research funds for the central universities": "Fundamental Research Funds for the Central Universities",
    "ministry of science and technology of the people's republic of china": "Ministry of Science and Technology of China",
    "ministry of education of the people's republic of china": "Ministry of Education of China",
    "national science and technology council": "National Science and Technology Council (Taiwan)",
    "ministry of science and technology, taiwan": "Ministry of Science and Technology (Taiwan)",
    # США
    "national institutes of health": "National Institutes of Health (NIH)",
    "hhs | national institutes of health (nih)": "National Institutes of Health (NIH)",
    "national institute of general medical sciences": "NIH — NIGMS",
    "national institute on drug abuse": "NIH — NIDA",
    "national institute of diabetes and digestive and kidney diseases": "NIH — NIDDK",
    "national institute on aging": "NIH — NIA",
    "national cancer institute": "NIH — NCI",
    "national institute of allergy and infectious diseases": "NIH — NIAID",
    "national science foundation": "National Science Foundation (NSF)",
    # Корея
    "national research foundation of korea": "National Research Foundation of Korea (NRF)",
    "national research foundation of korea (nrf)": "National Research Foundation of Korea (NRF)",
    "ministry of science and ict": "Ministry of Science and ICT (Korea)",
    # Бразилия
    "conselho nacional de desenvolvimento científico e tecnológico": "CNPq (Brazil)",
    "coordenação de aperfeiçoamento de pessoal de nível superior": "CAPES (Brazil)",
    "fundação de amparo à pesquisa do estado de são paulo": "FAPESP (Brazil)",
    # Европа
    "european union": "European Union",
    "european regional development fund": "European Regional Development Fund (ERDF)",
    "deutsche forschungsgemeinschaft": "DFG (Germany)",
    "deutsche forschungsgemeinschaft (dfg, german research foundation)": "DFG (Germany)",
    "instituto de salud carlos iii": "Instituto de Salud Carlos III (Spain)",
    # Другие
    "canadian institutes of health research": "Canadian Institutes of Health Research (CIHR)",
    "national health and medical research council": "NHMRC (Australia)",
    "japan society for the promotion of science": "JSPS (Japan)",
    "university grants commission": "University Grants Commission (India)",
    "indian council of medical research": "ICMR (India)",
}


def normalize_funder(raw: str) -> str | None:
    """Очищает имя фандера до каноничного или None."""
    if not raw or not isinstance(raw, str):
        return None
    name = raw

    # 1. Убираем http://dx.doi.org/10.13039/...
    name = re.sub(r"https?://dx\.doi\.org/10\.13039/\d+", "", name)
    # 2. Убираем 10.13039/... в любом месте
    name = re.sub(r"10\.13039/\d+", "", name)
    # 3. Убираем вообще URLs
    name = re.sub(r"https?://\S+", "", name)
    # 4. Убираем хвосты типа "10.xxxx/xxx"
    name = re.sub(r"\b10\.\d{4,}/\S*", "", name)
    # 5. Убираем цифры в начале
    name = re.sub(r"^\d+\.?\s*", "", name)
    # 6. Сжимаем пробелы
    name = re.sub(r"\s+", " ", name).strip()
    # 7. Убираем ведущее "the "/"The "
    name = re.sub(r"^(the|The)\s+", "", name)
    # 8. Убираем конечные точки/запятые
    name = name.rstrip(".,;:").strip()

    if not (3 < len(name) < 200):
        return None

    # 9. Канонизация по словарю
    key = name.lower().strip()
    if key in CANON:
        return CANON[key]

    # 10. Fuzzy: ищем частичное совпадение по первым 40 символам
    key40 = key[:40]
    for frag, canon in CANON.items():
        if frag[:40] in key40 or key40 in frag[:40]:
            return canon

    # 11. Убираем аббревиатуры в скобках для чистоты
    name = re.sub(r"\s*\([A-Z]{2,8}\)\s*$", "", name).strip()

    return name


# Страны — расширенный список с альтернативными названиями
COUNTRY_PATTERNS = {
    "China": r"\b(China|P\.?R\.?\s*China|Chinese)\b",
    "USA": r"\b(USA|U\.?S\.?A\.?|United States)\b",
    "UK": r"\b(UK|U\.?K\.?|United Kingdom|England|Scotland|Wales)\b",
    "Italy": r"\b(Italy|Italian)\b",
    "India": r"\b(India|Indian)\b",
    "Poland": r"\b(Poland|Polish)\b",
    "Spain": r"\b(Spain|Spanish)\b",
    "Korea": r"\b(Korea|Korean|South Korea)\b",
    "Germany": r"\b(Germany|German)\b",
    "Australia": r"\b(Australia|Australian)\b",
    "Japan": r"\b(Japan|Japanese)\b",
    "Iran": r"\b(Iran|Iranian)\b",
    "Canada": r"\b(Canada|Canadian)\b",
    "France": r"\b(France|French)\b",
    "Brazil": r"\b(Brazil|Brazilian)\b",
    "Netherlands": r"\b(Netherlands|Dutch)\b",
    "Switzerland": r"\b(Switzerland|Swiss)\b",
    "Egypt": r"\b(Egypt|Egyptian)\b",
    "Turkey": r"\b(Turkey|Turkish)\b",
    "Norway": r"\b(Norway|Norwegian)\b",
    "Russia": r"\b(Russia|Russian Federation|Russian)\b",
    "Taiwan": r"\b(Taiwan|Taiwanese)\b",
    "Mexico": r"\b(Mexico|Mexican)\b",
    "Saudi Arabia": r"\b(Saudi Arabia|Saudi)\b",
    "Israel": r"\b(Israel|Israeli)\b",
    "Sweden": r"\b(Sweden|Swedish)\b",
    "Denmark": r"\b(Denmark|Danish)\b",
    "Belgium": r"\b(Belgium|Belgian)\b",
    "Austria": r"\b(Austria|Austrian)\b",
    "Greece": r"\b(Greece|Greek)\b",
    "Portugal": r"\b(Portugal|Portuguese)\b",
    "Finland": r"\b(Finland|Finnish)\b",
}
COUNTRY_RE = {c: re.compile(p, re.IGNORECASE) for c, p in COUNTRY_PATTERNS.items()}


def detect_countries(affs: list[str]) -> set[str]:
    found = set()
    for a in affs:
        for c, rx in COUNTRY_RE.items():
            if rx.search(a):
                found.add(c)
    return found


def main() -> int:
    meta = json.loads(META.read_text(encoding="utf-8"))
    print(f"Всего статей: {len(meta)}\n")

    # ===== FUNDERS =====
    funders = Counter()
    for r in meta.values():
        seen_in_paper = set()  # не считаем одного фандера дважды в одной статье
        for src in r.get("funding_sources", []):
            name = normalize_funder(src)
            if name and name not in seen_in_paper:
                funders[name] += 1
                seen_in_paper.add(name)

    print(f"=== ТОП-25 FUNDERS (после нормализации) ===")
    for name, n in funders.most_common(25):
        print(f"{n:5}  {name}")

    # ===== COUNTRIES =====
    countries = Counter()
    for r in meta.values():
        affs = r.get("affiliations", []) or []
        for c in detect_countries(affs):
            countries[c] += 1

    print(f"\n=== ТОП-20 СТРАН (по affiliations) ===")
    for c, n in countries.most_common(20):
        print(f"{n:5}  {c}")

    # ===== Summary =====
    with_fund = sum(1 for r in meta.values() if r.get("has_funding"))
    with_coi = sum(1 for r in meta.values() if r.get("has_coi"))
    total = len(meta)
    print(f"\n=== SUMMARY ===")
    print(f"Всего статей:  {total}")
    print(f"С funding:     {with_fund} ({with_fund/total*100:.1f}%)")
    print(f"С COI:         {with_coi} ({with_coi/total*100:.1f}%)")

    # ===== По годам =====
    print(f"\n=== FUNDING RATE ПО ГОДАМ ===")
    by_year: dict[str, list[bool]] = {}
    for r in meta.values():
        y = r.get("year", "")
        if y and y.isdigit() and len(y) == 4:
            by_year.setdefault(y, []).append(r.get("has_funding", False))
    for y in sorted(by_year.keys()):
        vals = by_year[y]
        if len(vals) >= 20:
            rate = sum(vals) / len(vals) * 100
            print(f"{y}:  {len(vals):4} статей, {rate:5.1f}% с funding")

    # ===== CSV =====
    with OUT_FUND.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["funder", "papers"])
        for name, n in funders.most_common(200):
            w.writerow([name, n])

    with OUT_CTRY.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["country", "papers"])
        for name, n in countries.most_common(100):
            w.writerow([name, n])

    print(f"\n[OK] CSV: {OUT_FUND}")
    print(f"[OK] CSV: {OUT_CTRY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())