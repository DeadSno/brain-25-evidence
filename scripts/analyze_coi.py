"""Анализ Conflict of Interest (COI), funding и фарм-связей в full texts.

Проходит по data/pmc/text/*.xml и *.txt, извлекает:
- fn-type="conflict" (JATS EBI)
- <conflict> / <coi-statement> (NCBI PMC)
- <funding-source>, <ack> — финансирование
- <funding-statement> — общий текст гранта

Классифицирует COI по ключевым словам:
- none     — «no conflict», «nothing to disclose»
- yes      — «received honoraria», «consultant», «stock», ...
- unclear  — COI есть, но не классифицируется
- missing  — COI-секции нет вообще

Вывод:
    reports/coi_report.json  — агрегированные данные + samples
    stdout                   — краткая сводка

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

# --- Регулярки для извлечения блоков ---
RE_COI_FN = re.compile(
    r'<fn[^>]*fn-type="conflict"[^>]*>(.*?)</fn>',
    re.DOTALL | re.IGNORECASE,
)
RE_CONFLICT = re.compile(
    r"<conflict[^>]*>(.*?)</conflict>",
    re.DOTALL | re.IGNORECASE,
)
RE_COI_STMT = re.compile(
    r"<coi-statement[^>]*>(.*?)</coi-statement>",
    re.DOTALL | re.IGNORECASE,
)
RE_FUNDING_SRC = re.compile(
    r"<funding-source[^>]*>(.*?)</funding-source>",
    re.DOTALL | re.IGNORECASE,
)
RE_FUNDING_STMT = re.compile(
    r"<funding-statement[^>]*>(.*?)</funding-statement>",
    re.DOTALL | re.IGNORECASE,
)
RE_ACK = re.compile(
    r"<ack[^>]*>(.*?)</ack>",
    re.DOTALL | re.IGNORECASE,
)

# --- Классификация COI ---
COI_NONE = re.compile(
    r"\b(no conflicts? of interest|no competing interests?|"
    r"nothing to disclose|no conflict|declares? no|"
    r"has no conflict|none declared|no relevant|"
    r"authors declare no|the authors have no)\b",
    re.IGNORECASE,
)
COI_YES = re.compile(
    r"\b(received .{0,60}(honoraria|grant|funding|support|fees|payment)|"
    r"serves? as .{0,30}(consultant|advisor|advisory)|"
    r"advisory board|speaker.{0,20}fee|"
    r"stock|equity|shareholder|patent|"
    r"is an employee|employees of|"
    r"fees from|honoraria from|grants? from)\b",
    re.IGNORECASE,
)

# --- Фарм-компании ---
PHARMA = re.compile(
    r"\b("
    r"Pfizer|Merck|Novartis|Roche|Bayer|AstraZeneca|GSK|GlaxoSmithKline|"
    r"Johnson\s*&\s*Johnson|Janssen|Sanofi|Abbott|AbbVie|Amgen|"
    r"Boehringer|Eli\s+Lilly|Lilly|Bristol[- ]Myers|BMS|"
    r"Takeda|Teva|Novo\s+Nordisk|Sandoz|Mylan|"
    r"Danone|Nestl[eé]|Unilever|Herbalife|Amway|"
    r"DSM|BASF|DuPont|Kemin|Sabinsa"
    r")\b",
    re.IGNORECASE,
)


def strip_tags(s: str) -> str:
    """Убирает XML-теги и лишние пробелы."""
    return re.sub(r"<[^>]+>", " ", s).strip()


def analyze_file(path: Path) -> dict | None:
    """Разбирает один файл. Возвращает dict с результатами."""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    is_xml = path.suffix.lower() == ".xml"
    coi_texts: list[str] = []
    funding_texts: list[str] = []
    funder_names: list[str] = []

    if is_xml:
        for regex in (RE_COI_FN, RE_CONFLICT, RE_COI_STMT):
            for m in regex.finditer(txt):
                coi_texts.append(strip_tags(m.group(1)))

        for regex in (RE_FUNDING_SRC, RE_FUNDING_STMT, RE_ACK):
            for m in regex.finditer(txt):
                funding_texts.append(strip_tags(m.group(1)))

        # Отдельно — имена funder'ов
        for m in RE_FUNDING_SRC.finditer(txt):
            name = strip_tags(m.group(1))
            if 2 <= len(name) <= 200:
                funder_names.append(name)

    coi_joined = " ".join(coi_texts)
    fund_joined = " ".join(funding_texts)

    has_coi = bool(coi_texts)
    has_funding = bool(funding_texts)

    if has_coi:
        if COI_NONE.search(coi_joined):
            coi_type = "none"
        elif COI_YES.search(coi_joined):
            coi_type = "yes"
        else:
            coi_type = "unclear"
    else:
        coi_type = "missing"

    has_pharma = bool(PHARMA.search(coi_joined + " " + fund_joined))

    return {
        "file": path.name,
        "is_xml": is_xml,
        "has_coi": has_coi,
        "coi_type": coi_type,
        "has_funding": has_funding,
        "has_pharma": has_pharma,
        "funders": funder_names[:5],  # до 5 имён на файл
    }


def main() -> int:
    files = sorted(TEXT_DIR.glob("*.xml")) + sorted(TEXT_DIR.glob("*.txt"))
    print(f"Файлов к обработке: {len(files)}\n")

    results: list[dict] = []
    funder_counter: Counter = Counter()

    for i, f in enumerate(files, 1):
        r = analyze_file(f)
        if not r:
            continue
        results.append(r)
        for name in r["funders"]:
            # Нормализуем регистр
            key = name.strip()[:120]
            funder_counter[key] += 1

        if i % 2000 == 0:
            print(f"  [{i}/{len(files)}]")

    n = len(results)
    if n == 0:
        print("[!] Нет данных")
        return 1

    # Подсчёт
    xml_count = sum(1 for r in results if r["is_xml"])
    txt_count = n - xml_count

    coi_counts = Counter(r["coi_type"] for r in results)
    coi_yes = coi_counts.get("yes", 0)
    coi_none = coi_counts.get("none", 0)
    coi_unclear = coi_counts.get("unclear", 0)
    coi_missing = coi_counts.get("missing", 0)

    has_funding = sum(1 for r in results if r["has_funding"])
    has_pharma = sum(1 for r in results if r["has_pharma"])

    # Среди тех, кто указал COI — сколько реально имеют конфликт
    declared = coi_yes + coi_none + coi_unclear
    yes_share = (coi_yes / declared * 100) if declared else 0

    report = {
        "total_files": n,
        "files_by_type": {"xml": xml_count, "txt": txt_count},
        "coi": {
            "declared_yes": coi_yes,
            "declared_none": coi_none,
            "unclear": coi_unclear,
            "missing": coi_missing,
            "declared_total": declared,
            "yes_share_of_declared_pct": round(yes_share, 2),
        },
        "funding": {
            "has_funding_section": has_funding,
            "pct": round(has_funding / n * 100, 2),
        },
        "pharma_mention": {
            "count": has_pharma,
            "pct": round(has_pharma / n * 100, 2),
        },
        "top_funders": dict(funder_counter.most_common(30)),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # --- Сводка в stdout ---
    print(f"\n=== Результаты ===")
    print(f"Всего файлов:               {n}")
    print(f"  XML:                      {xml_count}")
    print(f"  TXT:                      {txt_count}")
    print()
    print(f"COI — указан конфликт:      {coi_yes:>6} ({coi_yes/n*100:.1f}%)")
    print(f"COI — нет конфликта:        {coi_none:>6} ({coi_none/n*100:.1f}%)")
    print(f"COI — неясно:               {coi_unclear:>6} ({coi_unclear/n*100:.1f}%)")
    print(f"COI — отсутствует вообще:   {coi_missing:>6} ({coi_missing/n*100:.1f}%)")
    print()
    print(f"Указан funding:             {has_funding:>6} ({has_funding/n*100:.1f}%)")
    print(f"Упомянута фарм-компания:    {has_pharma:>6} ({has_pharma/n*100:.1f}%)")
    print()
    print(f"Среди указавших COI ({declared} шт):")
    print(f"  доля с реальным конфликтом: {yes_share:.1f}%")
    print()
    print("Топ-10 funders:")
    for name, cnt in funder_counter.most_common(10):
        print(f"  {cnt:>4}  {name[:80]}")

    print(f"\n[OK] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())