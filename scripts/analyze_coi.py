"""Анализ Conflict of Interest (COI) и funding в real full texts.

Работает по XML >20KB (front matter + abstract отсеиваем).
COI ищется как:
  1. Структурно: <fn fn-type="conflict">, <sec sec-type="COI">
  2. Как текст: "conflict of interest", "competing interest",
     "declaration of interest", "financial disclosure"

Классификация:
  none     — "no conflict", "none of the authors", "nothing to disclose"
  yes      — "received honoraria", "consultant", "stock", "patent"
  unclear  — COI упомянут, но не классифицируется однозначно
  missing  — упоминаний нет

Запуск:
    python scripts/analyze_coi.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_DIR = ROOT / "data" / "pmc" / "text"
OUT = ROOT / "reports" / "coi_report.json"

MIN_SIZE = 20_000  # меньше — это front matter, не full text

# --- Структурные паттерны JATS ---
RE_FN_CONFLICT = re.compile(
    r'<fn[^>]*fn-type="conflict"[^>]*>(.*?)</fn>',
    re.DOTALL | re.IGNORECASE,
)
RE_SEC_COI = re.compile(
    r'<sec[^>]*sec-type="(?:COI|conflict)[^"]*"[^>]*>(.*?)</sec>',
    re.DOTALL | re.IGNORECASE,
)
RE_CONFLICT_TAG = re.compile(
    r"<conflict[^>]*>(.*?)</conflict>",
    re.DOTALL | re.IGNORECASE,
)

# --- Свободный текст: ищем маркеры COI ---
COI_MARKERS = re.compile(
    r"conflicts? of interest|competing interests?|"
    r"declarations? of interest|financial disclosure|"
    r"conflicts? of interests?|competing financial interests?",
    re.IGNORECASE,
)

# --- Funding: структурно и как текст ---
RE_FUNDING_SRC = re.compile(
    r"<funding-source[^>]*>(.*?)</funding-source>",
    re.DOTALL | re.IGNORECASE,
)
RE_FUNDING_STMT = re.compile(
    r"<funding-statement[^>]*>(.*?)</funding-statement>",
    re.DOTALL | re.IGNORECASE,
)
RE_FUNDING_WORD = re.compile(
    r"[^.<>]{0,200}(?:this (?:work|study) was (?:funded|supported)|"
    r"supported by (?:grant|funding)|funded by)[^.<>]{0,300}",
    re.IGNORECASE,
)

# --- Классификация по ключевым словам ---
NEGATIVE = re.compile(
    r"\b("
    r"no\s+(?:potential\s+)?conflicts?|no\s+competing|"
    r"nothing to disclose|declares? no|declare no|"
    r"none of the authors|no financial|no relevant|"
    r"authors have no|no conflict|not have any|"
    r"no competing financial|"
    # Добавлено: «none declared», «none to declare», «none reported»
    r"none (?:declared|to declare|reported|disclosed)|"
    r"no interests? (?:to declare|declared)|"
    r"nothing (?:declared|to declare|reported)|"
    r"no personal (?:financial )?interests?"
    r")\b",
    re.IGNORECASE,
)
# Настоящий COI — личная выгода автора (НЕ funding исследования)
POSITIVE = re.compile(
    r"\b("
    # Личные выплаты
    r"received .{0,60}(honoraria|speaker.{0,20}fee|consulting fee|"
    r"consultancy fee|personal fee|payment for lecture)|"
    r"honoraria from|fees from|"
    # Роли в компаниях
    r"serves? as .{0,30}(consultant|advisor|advisory)|"
    r"advisory board|board member|"
    r"consultant for|consulting fees|"
    # Владение
    r"stock|equity|shareholder|shareholders|stockholder|"
    r"patent(s)? (?:holder|pending)|"
    # Работа
    r"is an employee|are employees|employee of|"
    r"employed by .{0,40}(Inc|Ltd|LLC|Corp|GmbH|SA|AG)|"
    # (двусмысленные убраны: могут совпасть с negative-формулировками)
    r"has a financial interest|has financial interests|"
    r"holds? (?:stock|equity|shares?)|"
    r"received (?:speaker|consulting|consultancy) fees?"
    r")\b",
    re.IGNORECASE,
)

PHARMA = re.compile(
    r"\b(Pfizer|Merck|Novartis|Roche|Bayer|AstraZeneca|GSK|"
    r"GlaxoSmithKline|Johnson\s*&\s*Johnson|Janssen|Sanofi|"
    r"Abbott|AbbVie|Amgen|Boehringer|Eli\s+Lilly|"
    r"Bristol[- ]Myers|Takeda|Teva|Novo\s+Nordisk|"
    r"Danone|Nestl[eé]|Unilever|Herbalife|Amway|"
    r"Sabinsa|DSM|BASF|Kemin)\b",
    re.IGNORECASE,
)


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_coi_windows(txt: str, before: int = 100, after: int = 800) -> list[str]:
    """O(n): маркеры через finditer, окно before/after символов.

    after=800 — захватываем текст декларации после заголовка
    ('Competing interests: The authors declare no...')
    before=100 — контекст перед заголовком
    """
    results = []
    for m in COI_MARKERS.finditer(txt):
        start = max(0, m.start() - before)
        end = min(len(txt), m.end() + after)
        results.append(txt[start:end])
    return results


def extract_coi_texts(txt: str) -> tuple[list[str], list[str]]:
    """Возвращает (coi_blocks, funding_blocks) — список текстов."""
    coi_blocks: list[str] = []
    fund_blocks: list[str] = []

    # 1. Структурные блоки COI
    for regex in (RE_FN_CONFLICT, RE_SEC_COI, RE_CONFLICT_TAG):
        for m in regex.finditer(txt):
            coi_blocks.append(strip_tags(m.group(1)))

    # 2. Текстовые упоминания — окно 100/800
    for window in extract_coi_windows(txt, before=100, after=800):
        coi_blocks.append(strip_tags(window))

    # 3. Funding
    for regex in (RE_FUNDING_SRC, RE_FUNDING_STMT):
        for m in regex.finditer(txt):
            fund_blocks.append(strip_tags(m.group(1)))
    for m in RE_FUNDING_WORD.finditer(txt):
        fund_blocks.append(strip_tags(m.group(0)))

    return coi_blocks, fund_blocks


def classify_coi(coi_blocks: list[str]) -> tuple[str, str]:
    """Возвращает (type, sample_text).

    Разбивает блоки на предложения, каждое классифицирует независимо:
      - есть хоть одно positive → yes (у одного из авторов конфликт)
      - только negative → none
      - ни то, ни другое → unclear
      - пусто → missing
    """
    if not coi_blocks:
        return "missing", ""

    sample = coi_blocks[0][:300]

    # Разбиваем каждый блок на предложения
    sentences: list[str] = []
    for block in coi_blocks:
        # Грубое деление по ., ;, новым строкам
        for s in re.split(r"[.;\n]+", block):
            s = s.strip()
            if len(s) >= 5:
                sentences.append(s)

    has_positive = False
    has_negative = False
    for s in sentences:
        # Если в предложении есть negation — оно negative, даже если есть грант
        if NEGATIVE.search(s):
            has_negative = True
            continue
        if POSITIVE.search(s):
            has_positive = True

    # Логика:
    # — хоть одно положительное → yes (личный конфликт хотя бы у одного автора)
    # — только негативные → none
    # — пусто → unclear
    if has_positive:
        return "yes", sample
    if has_negative:
        return "none", sample
    return "unclear", sample


def analyze_file(path: Path) -> dict | None:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    coi_blocks, fund_blocks = extract_coi_texts(txt)
    coi_type, sample = classify_coi(coi_blocks)

    # Dedup funding, join
    fund_joined = " ".join(fund_blocks)
    funders = [strip_tags(m.group(1))[:120]
               for m in RE_FUNDING_SRC.finditer(txt)
               if 2 <= len(strip_tags(m.group(1))) <= 200]

    has_pharma = bool(PHARMA.search(" ".join(coi_blocks) + " " + fund_joined))

    return {
        "file": path.name,
        "size": path.stat().st_size,
        "coi_type": coi_type,
        "coi_sample": sample,
        "n_coi_blocks": len(coi_blocks),
        "has_funding": bool(fund_blocks),
        "n_funding_blocks": len(fund_blocks),
        "has_pharma": has_pharma,
        "funders": funders[:5],
    }


def main() -> int:
    all_xml = sorted(TEXT_DIR.glob("*.xml"))
    files = [f for f in all_xml if f.stat().st_size >= MIN_SIZE]
    print(f"XML всего:          {len(all_xml)}")
    print(f"XML >= {MIN_SIZE//1000}KB (full text): {len(files)}")
    print(f"Отсеяно (front matter):  {len(all_xml) - len(files)}\n")

    results: list[dict] = []
    funder_counter: Counter = Counter()

    for i, f in enumerate(files, 1):
        r = analyze_file(f)
        if not r:
            continue
        results.append(r)
        for name in r["funders"]:
            key = name.strip()[:100]
            funder_counter[key] += 1
        if i % 1000 == 0:
            print(f"  [{i}/{len(files)}]")

    n = len(results)
    if n == 0:
        print("[!] Нет данных")
        return 1

    coi_counts = Counter(r["coi_type"] for r in results)
    coi_yes = coi_counts.get("yes", 0)
    coi_none = coi_counts.get("none", 0)
    coi_unclear = coi_counts.get("unclear", 0)
    coi_missing = coi_counts.get("missing", 0)
    declared = coi_yes + coi_none + coi_unclear

    has_funding = sum(1 for r in results if r["has_funding"])
    has_pharma = sum(1 for r in results if r["has_pharma"])

    # Собираем примеры по каждой категории
    samples = {
        "yes": [r["coi_sample"] for r in results if r["coi_type"] == "yes"][:5],
        "none": [r["coi_sample"] for r in results if r["coi_type"] == "none"][:5],
        "unclear": [r["coi_sample"] for r in results if r["coi_type"] == "unclear"][:5],
    }

    report = {
        "total_full_texts": n,
        "total_xml": len(all_xml),
        "threshold_bytes": MIN_SIZE,
        "coi": {
            "declared_yes": coi_yes,
            "declared_none": coi_none,
            "unclear": coi_unclear,
            "missing": coi_missing,
            "declared_total": declared,
            "declared_pct": round(declared / n * 100, 2),
            "yes_share_of_declared_pct": round(
                coi_yes / declared * 100 if declared else 0, 2
            ),
        },
        "funding": {
            "count": has_funding,
            "pct": round(has_funding / n * 100, 2),
        },
        "pharma": {
            "count": has_pharma,
            "pct": round(has_pharma / n * 100, 2),
        },
        "top_funders": dict(funder_counter.most_common(30)),
        "samples": samples,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")

    print(f"\n=== Результаты ({n} full texts) ===")
    print(f"COI — указан конфликт:      {coi_yes:>6} ({coi_yes/n*100:.1f}%)")
    print(f"COI — нет конфликта:        {coi_none:>6} ({coi_none/n*100:.1f}%)")
    print(f"COI — неясно:               {coi_unclear:>6} ({coi_unclear/n*100:.1f}%)")
    print(f"COI — отсутствует:          {coi_missing:>6} ({coi_missing/n*100:.1f}%)")
    print(f"  Всего указавших COI:      {declared:>6} ({declared/n*100:.1f}%)")
    print()
    print(f"Указан funding:             {has_funding:>6} ({has_funding/n*100:.1f}%)")
    print(f"Упомянута фарм-компания:    {has_pharma:>6} ({has_pharma/n*100:.1f}%)")
    print()
    if declared:
        print(f"Из указавших COI ({declared}):")
        print(f"  реальный конфликт (yes):  {coi_yes/n*100:.1f}% от всех")
    print()
    print("Топ-10 funders:")
    for name, cnt in funder_counter.most_common(10):
        print(f"  {cnt:>4}  {name[:80]}")
    print(f"\n[OK] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())