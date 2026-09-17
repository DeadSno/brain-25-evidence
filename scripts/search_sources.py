"""Поиск PMID через PubMed E-utilities для карточек без key_sources.

Использование:
    python scripts/search_sources.py --list
    python scripts/search_sources.py "Гинкго"
    python scripts/search_sources.py --all-missing

Два режима:
  1) CURATED — если карточка есть в MANUAL_PMIDS: esearch не зовётся,
     берём ровно указанные PMID через esummary. Это гарантирует точность.
  2) AUTO — для новых карточек: esearch по PUBMED_QUERIES +
     title-фильтр по TITLE_TERMS / EXCLUDE_TERMS.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "brain-25-evidence/1.0"


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _get(url: str, retries: int = 3) -> str:
    """GET с ретраями на 429/5xx."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Failed after {retries} attempts: {url} ({last_exc})")


# ---------------------------------------------------------------------------
# E-utilities
# ---------------------------------------------------------------------------

def esearch(term: str, retmax: int = 15) -> list[str]:
    """esearch → список PMID."""
    q = urllib.parse.quote(term)
    url = (
        f"{EUTILS}/esearch.fcgi?db=pubmed&term={q}"
        f"&retmode=json&retmax={retmax}&sort=relevance"
    )
    raw = _get(url)
    data = json.loads(raw)
    ids = data.get("esearchresult", {}).get("idlist", []) or []
    return [str(pid) for pid in ids if str(pid).strip()]


def _safe_year(pubdate: str | None) -> int:
    """'2024 Jan-Feb' → 2024; '?' / None / '' → 0."""
    if not pubdate:
        return 0
    head = str(pubdate)[:4]
    return int(head) if head.isdigit() else 0


def esummary(pmids: list[str]) -> dict[str, dict]:
    """esummary → метаданные (title, year, journal, pubtype)."""
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    raw = _get(url)
    data = json.loads(raw).get("result", {}) or {}
    result: dict[str, dict] = {}
    for pmid in pmids:
        info = data.get(pmid)
        if not isinstance(info, dict):
            continue
        if info.get("error"):
            continue
        result[pmid] = {
            "title": info.get("title") or "?",
            "year": _safe_year(info.get("pubdate")),
            "journal": info.get("fulljournalname") or "?",
            "pubtype": list(info.get("pubtype") or []),
        }
    return result


# ---------------------------------------------------------------------------
# CURATED PMID — вручную отобранные источники для существующих карточек
# ---------------------------------------------------------------------------
# Если карточка здесь есть — esearch не вызывается, возвращаются ровно
# эти PMID в указанном порядке. Порядок = приоритет (сначала самое важное).
# Обновлять вручную при ревизии evidence base.

MANUAL_PMIDS: dict[str, list[str]] = {
    "Гинкго": [
        "39895346",  # EGb 761 mild dementia, meta-analysis 2025
        "38718890",  # unstable angina, SR+NMA 2024
        "32349519",  # acute ischemic stroke, SR+MA 2020
        "26979525",  # tardive dyskinesia, MA 2016
        "25114079",  # cognitive impairment & dementia, SR+MA 2015
    ],
    "Alpha-GPC": [
        "41426989",  # choline alphoscerate vs citicoline, SR+MA 2025
        "36683513",  # adult-onset cognitive dysfunctions, SR+MA 2023
        "39703111",  # T2D cognitive function, RCT 2025
        "39683633",  # acute Alpha-GPC healthy men, RCT 2024
        "38875437",  # + donepezil combo, RCT 2024
    ],
    "B12": [
        "38231320",  # routes of supplementation, SR+NMA 2024
        "39373282",  # B12 status in adult vegans, SR+MA 2024
        "38189492",  # pregnancy, Cochrane SR 2024
        "37060552",  # PPI-induced deficiency, SR+MA 2023
        "33809274",  # cognition, depression, fatigue, SR+MA 2021
    ],
    "Цинк": [
        "38719213",  # common cold, Cochrane 2024
        "39641338",  # diarrhoea in children, SR+MA 2024
        "39683510",  # primary dysmenorrhea, SR+MA 2024
        "36577241",  # serum zinc ↔ testosterone, SR 2023
        "37836377",  # pediatric GI diseases, SR 2023
    ],
    "Глицин": [
        "37851316",  # glycine administration, SR human adults 2024
        "41109034",  # enteral glycine, RCT critically ill 2025
        "35975308",  # GlyNAC older adults, RCT 2023
    ],
    "Биотин": [
        "36386951",  # T2D glycemic control, SR+MA 2022
        "27362288",  # biotin immunoassay interference, review 2016
        "33171595",  # PROVIT depression B7, RCT 2020
        "11815321",  # marginal biotin deficiency pregnancy 2002
        "7840079",   # biotin supplementation protein-energy malnutrition 1995
    ],
    "Пустырник": [
        "23042598",  # Leonurus cardiaca phytochemistry review 2013
        "33494336",  # phytochemical profile & activities 2021
        "24841965",  # herb extract & mitochondrial oxphos 2014
        "20839214",  # oil extract arterial hypertension + anxiety 2011
        "19918711",  # cardiac & electrophysiological effects 2010
    ],
    "D-манноза": [
        "41004704",  # rUTI prophylaxis, SR+MA 2025
        "36041061",  # Cochrane UTI 2022
        "32972899",  # rUTI prevention, SR 2021
        "32497610",  # vs other agents, SR+MA 2020
        "40853430",  # hydration vs D-mannose vs antibiotics, RCT 2026
    ],
    "Йохимбин": [
        "9649257",   # ED, SR+MA 1998
        "8836468",   # erectile disorder, meta-analytic 1996
        "35162339",  # sprint performance, RCT 2022
        "23559222",  # norepinephrine + impulsivity, RCT 2013
        "17214405",  # body composition in soccer players, RCT 2006
    ],
    "Трибулус": [
        "40360723",  # ED management, SR+MA 2026
        "40219032",  # ED + testosterone in men, SR 2025
        "35954909",  # sport & health biomarkers, SR 2022
        "32736394",  # female sexual dysfunction, SR 2020
        "24559105",  # aphrodisiac & performance, SR 2014
    ],
    "Хлорофилл": [
        "25844615",  # topical copper chlorophyllin, RCT 2015
        "21541030",  # chlorophyllin colorectal DNA damage, RCT 2011
        "16417778",  # sodium copper chlorophyllin, leukopenia, RCT 2005
        "12628519",  # chemoprevention aflatoxin, RCT 2003
        "11724948",  # chlorophyllin aflatoxin-DNA adducts, RCT 2001
    ],
}


# ---------------------------------------------------------------------------
# Словари автопоиска (fallback для карточек без MANUAL_PMIDS)
# ---------------------------------------------------------------------------

PUBMED_QUERIES: dict[str, str] = {
    "Гинкго":    '(ginkgo biloba[tiab]) AND (supplement*[tiab] OR extract[tiab])',
    "Alpha-GPC": '(alpha-glycerylphosphorylcholine[tiab] OR choline alphoscerate[tiab] OR choline alfoscerate[tiab])',
    "Цинк":      '(zinc[tiab]) AND (supplement*[tiab] OR deficiency[tiab] OR immune[tiab])',
    "B12":       '(vitamin b12[tiab] OR cobalamin[tiab] OR cyanocobalamin[tiab]) AND (deficiency[tiab] OR supplement*[tiab] OR cognitive[tiab])',
    "Глицин":    '(glycine[tiab]) AND (supplement*[tiab] OR sleep[tiab] OR cognitive[tiab])',
    "Биотин":    '(biotin[tiab] OR "vitamin B7"[tiab]) AND (supplement*[tiab] OR deficiency[tiab])',
    "Пустырник": '(leonurus[tiab] OR "motherwort"[tiab]) AND (anxiolytic[tiab] OR sedative[tiab] OR cardiac[tiab])',
    "D-манноза": '("D-mannose"[tiab]) AND (urinary[tiab] OR "UTI"[tiab] OR "E. coli"[tiab])',
    "Йохимбин":  '(yohimbine[tiab]) AND (performance[tiab] OR "fat loss"[tiab] OR erectile[tiab])',
    "Трибулус":  '("Tribulus terrestris"[tiab]) AND (testosterone[tiab] OR performance[tiab] OR libido[tiab])',
    "Хлорофилл": '(chlorophyllin[tiab] OR "copper chlorophyllin"[tiab] OR "sodium copper chlorophyllin"[tiab] OR (chlorophyll[tiab] AND supplement*[tiab]))',
}

ALIASES: dict[str, str] = {
    "ginkgo": "Гинкго",
    "ginkgo-biloba": "Гинкго",
    "ginkgo biloba": "Гинкго",
    "alpha-gpc": "Alpha-GPC",
    "alpha_gpc": "Alpha-GPC",
    "alphagpc": "Alpha-GPC",
    "b12": "B12",
    "vitamin-b12": "B12",
    "cobalamin": "B12",
    "zinc": "Цинк",
    "glycine": "Глицин",
    "biotin": "Биотин",
    "motherwort": "Пустырник",
    "leonurus": "Пустырник",
    "d-mannose": "D-манноза",
    "d_mannose": "D-манноза",
    "mannose": "D-манноза",
    "yohimbine": "Йохимбин",
    "tribulus": "Трибулус",
    "tribulus-terrestris": "Трибулус",
    "chlorophyll": "Хлорофилл",
    "chlorophyllin": "Хлорофилл",
}

TITLE_TERMS: dict[str, tuple[str, ...]] = {
    "Гинкго":    ("ginkgo", "egb 761", "egb-761"),
    "Alpha-GPC": (
        "alpha-gpc", "alpha glycerylphosphorylcholine", "glycerylphosphorylcholine",
        "choline alphoscerate", "choline alfoscerate", "cholinergic precursor",
    ),
    "Цинк":      ("zinc",),
    "B12":       ("vitamin b12", "cobalamin", "cyanocobalamin"),
    "Глицин":    ("glycine", "glynac"),
    "Биотин":    ("biotin", "vitamin b7"),
    "Пустырник": ("leonurus cardiaca", "motherwort"),
    "D-манноза": ("d-mannose", "mannose"),
    "Йохимбин":  ("yohimbine", "yohimbin"),
    "Трибулус":  ("tribulus",),
    "Хлорофилл": ("chlorophyllin", "copper chlorophyllin", "sodium copper chlorophyllin"),
}

EXCLUDE_TERMS: tuple[str, ...] = (
    # сельхоз-животные
    "cattle", "cow", "dairy", "calf", "calves",
    "pig", "piglet", "swine", "weanling",
    "poultry", "broiler", "hen", "chicken", "duck", "duckling",
    "fish", "shrimp", "aquaculture",
    # лабораторные животные
    "rat", "mouse", "mice", "murine", "zebrafish",
    # ботаника: совпадение с родом/видом (не БАД)
    "glycine max", "glycine soja",
)


def resolve_query(name: str) -> tuple[str, str] | None:
    """Найти PubMed-запрос для имени карточки. None, если ничего не нашли."""
    if not name:
        return None
    if name in PUBMED_QUERIES:
        return name, PUBMED_QUERIES[name]
    low = name.strip().lower()
    for key, q in PUBMED_QUERIES.items():
        if key.lower() == low:
            return key, q
    alias_key = ALIASES.get(low)
    if alias_key and alias_key in PUBMED_QUERIES:
        return alias_key, PUBMED_QUERIES[alias_key]
    return None


def resolve_manual(name: str) -> tuple[str, list[str]] | None:
    """Найти curated PMID-список. None, если карточки нет в MANUAL_PMIDS."""
    if not name:
        return None
    if name in MANUAL_PMIDS:
        return name, MANUAL_PMIDS[name]
    low = name.strip().lower()
    for key, pmids in MANUAL_PMIDS.items():
        if key.lower() == low:
            return key, pmids
    alias_key = ALIASES.get(low)
    if alias_key and alias_key in MANUAL_PMIDS:
        return alias_key, MANUAL_PMIDS[alias_key]
    return None


_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


def _term_pattern(term: str) -> re.Pattern[str]:
    pat = _PATTERN_CACHE.get(term)
    if pat is None:
        pat = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(term) + r"s?(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        _PATTERN_CACHE[term] = pat
    return pat


def _title_matches(title: str, terms: tuple[str, ...]) -> bool:
    if not terms:
        return False
    return any(_term_pattern(t).search(title) for t in terms)


def _title_excluded(title: str) -> bool:
    return any(_term_pattern(t).search(title) for t in EXCLUDE_TERMS)


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------

PRIORITY: dict[str, int] = {
    "Meta-Analysis": 3,
    "Systematic Review": 3,
    "Randomized Controlled Trial": 2,
    "Review": 1,
}


def find_sources(name: str, limit: int = 5) -> list[dict]:
    """Найти источники для добавки.

    Приоритет: MANUAL_PMIDS (curated) > автоматический поиск.
    Возвращает список словарей, отсортированный по приоритету.
    """
    # --- curated path ---
    manual = resolve_manual(name)
    if manual is not None:
        used_name, pmids = manual
        print(f"  [curated] {used_name}: {len(pmids)} PMID из MANUAL_PMIDS")
        meta = esummary(pmids)
        results: list[dict] = []
        for pmid in pmids:
            info = meta.get(pmid)
            if not info:
                print(f"  [!] PMID {pmid} не отдался — проверьте вручную",
                      file=sys.stderr)
                continue
            score = max(
                (PRIORITY.get(t, 0) for t in info.get("pubtype", [])),
                default=0,
            )
            results.append({
                "pmid": pmid,
                "score": score,
                "resolved_name": used_name,
                "source": "curated",
                **info,
            })
        return results[:limit]

    # --- auto path ---
    resolved = resolve_query(name)
    if resolved is None:
        print(
            f"  [!] нет PubMed-запроса для '{name}'. "
            f"Добавьте его в PUBMED_QUERIES/ALIASES или в MANUAL_PMIDS.",
            file=sys.stderr,
        )
        return []
    used_name, base_q = resolved

    queries = [
        f"({base_q}) AND (meta-analysis[pt] OR systematic review[pt])",
        f"({base_q}) AND randomized controlled trial[pt]",
        base_q,
    ]

    seen: set[str] = set()
    candidates: list[str] = []
    for q in queries:
        try:
            ids = esearch(q, retmax=15)
            print(f"  [q] {q[:80]}… → {len(ids)} PMID")
        except Exception as e:  # noqa: BLE001
            print(f"  [!] ошибка запроса: {e}", file=sys.stderr)
            continue
        for pid in ids:
            if pid not in seen:
                seen.add(pid)
                candidates.append(pid)
        time.sleep(0.4)
        if len(candidates) >= 25:
            break

    if not candidates:
        return []

    meta = esummary(candidates[:25])

    ranked: list[dict] = []
    for pid in candidates[:25]:
        info = meta.get(pid)
        if not info:
            continue
        score = max(
            (PRIORITY.get(t, 0) for t in info.get("pubtype", [])),
            default=0,
        )
        ranked.append({
            "pmid": pid, "score": score,
            "resolved_name": used_name, "source": "auto", **info,
        })

    ranked.sort(key=lambda x: (-x["score"], -x["year"]))

    terms = TITLE_TERMS.get(used_name, ())
    if not terms:
        return ranked[:limit]

    matching = [
        r for r in ranked
        if _title_matches(r["title"], terms) and not _title_excluded(r["title"])
    ]
    return matching[:limit]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_list() -> int:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    missing = [s for s in data if not s.get("key_sources")]
    print(f"Карточек без key_sources: {len(missing)}\n")
    for s in missing:
        sid = s.get("id", "")
        if resolve_manual(sid):
            mode = "curated"
        elif resolve_query(sid):
            mode = "auto"
        else:
            mode = "—"
        print(
            f"  {sid:25s} | grade={s.get('grade', '?'):3} "
            f"| metaCount={s.get('metaCount', 0):3} | {mode}"
        )
    return 0


def cmd_search(name: str) -> int:
    print(f"=== Поиск sources: {name} ===\n")
    results = find_sources(name)
    if not results:
        print("Ничего не найдено.")
        return 1
    for i, r in enumerate(results, 1):
        types = ", ".join(r["pubtype"]) or "—"
        print(f"{i}. PMID {r['pmid']} ({r['year']}) [{r['source']}] — {types}")
        print(f"   {r['title']}")
        print(f"   {r['journal']}")
        print()
    return 0


def cmd_all_missing() -> int:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    # Обрабатываем две группы:
    # 1) карточки без key_sources — изначально пустые
    # 2) карточки с MANUAL_PMIDS — пересборка, чтобы применить свежий curated-набор
    def _needs_rebuild(s: dict) -> bool:
        return (not s.get("key_sources")) or (resolve_manual(s.get("id", "")) is not None)

    cards = [s for s in data if _needs_rebuild(s)]
    print(f"Обрабатываю {len(cards)} карточек...\n")

    out: dict[str, list[dict]] = {}
    for s in cards:
        sid = s.get("id", "?")
        print(f"— {sid}")
        try:
            results = find_sources(sid)
            out[sid] = results
            print(f"  найдено: {len(results)}")
        except Exception as e:  # noqa: BLE001
            print(f"  [!] {e}", file=sys.stderr)
            out[sid] = []
        time.sleep(0.5)

    report = ROOT / "reports" / "sources_candidates.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[OK] Отчёт: {report}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PubMed source finder")
    parser.add_argument("name", nargs="?", help="название добавки")
    parser.add_argument("--list", action="store_true",
                        help="список карточек без sources")
    parser.add_argument("--all-missing", action="store_true",
                        help="обработать все карточки без key_sources")
    args = parser.parse_args()

    if args.list:
        return cmd_list()
    if args.all_missing:
        return cmd_all_missing()
    if args.name:
        return cmd_search(args.name)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())