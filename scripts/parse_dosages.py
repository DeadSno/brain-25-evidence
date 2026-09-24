"""Парсер dosage из data.json → dosage_parsed.json.

Извлекает min/max/unit/freq из строк вида:
  "3-5 г/сут (моногидрат)"     → {min:3, max:5, unit:"g", freq:"per_day"}
  "1000-2000 МЕ/сут"            → {min:1000, max:2000, unit:"IU"}
  "1-10 млрд КОЕ"               → {min:1e9, max:1e10, unit:"CFU"}
  "500-1000 мкг"                → {min:500, max:1000, unit:"mcg"}
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
OUT = ROOT / "docs" / "dosage_parsed.json"

# Единицы → канон
UNITS = {
    "г": "g", "гр": "g", "g": "g", "gram": "g",
    "мг": "mg", "mg": "mg",
    "мкг": "mcg", "mcg": "mcg", "ug": "mcg",
    "ме": "IU", "МЕ": "IU", "iu": "IU", "IU": "IU",
    "кое": "CFU", "КОЕ": "CFU", "cfu": "CFU",
    "млрд кое": "CFU_billion",
}

# Множители для млрд/млн
MULT = {"млрд": 1e9, "млн": 1e6, "тыс": 1e3}

# "per_day" маркеры
PER_DAY = ["/сут", "в сутки", "в день", "/день", "per day"]
SINGLE = ["за 30", "за час", "разово", "до задачи", "перед"]
PER_WEEK = ["/нед", "в неделю"]


def parse_dosage(text: str) -> dict | None:
    """Извлекает числовой диапазон + единицу."""
    if not text or not isinstance(text, str):
        return None

    lower = text.lower()

    # 1. Множитель (млрд / млн)
    mult = 1
    for k, v in MULT.items():
        if k in lower:
            mult = v
            break

    # 2. Частота
    freq = "per_day"  # дефолт для БАДов
    if any(m in lower for m in PER_WEEK):
        freq = "per_week"
    elif any(m in lower for m in SINGLE):
        freq = "single"
    elif any(m in lower for m in PER_DAY):
        freq = "per_day"

    # 3. Числа (диапазон или одно)
    # Ищем "X-Y", "X–Y", "X до Y"
    range_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)", text
    )
    if range_match:
        mn = float(range_match.group(1).replace(",", "."))
        mx = float(range_match.group(2).replace(",", "."))
    else:
        # Одно число
        single = re.search(r"(\d+(?:[.,]\d+)?)", text)
        if not single:
            return None
        mn = mx = float(single.group(1).replace(",", "."))

    # 4. Единица — ищем сразу после чисел
    unit = None
    # Проверяем после диапазона
    after = text[range_match.end() if range_match else 0:]
    for uname, ucanon in UNITS.items():
        if re.search(rf"\b{re.escape(uname)}\b", after[:30], re.IGNORECASE):
            unit = ucanon
            break

    # Fallback — общий поиск единицы в строке
    if not unit:
        for uname, ucanon in UNITS.items():
            if re.search(rf"\b{re.escape(uname)}\b", text, re.IGNORECASE):
                unit = ucanon
                break

    # 5. Множитель частоты: "2 раза/сут" → ×2, "2-3 раза/сут" → ×(2..3)
    m_range_times = re.search(
        r"(\d+)\s*[-–]\s*(\d+)\s*раз(?:а)?\s*/\s*сут", lower
    )
    m_single_times = re.search(
        r"(?<![-\d.])(\d+)\s*раз(?:а)?\s*/\s*сут", lower
    )
    if m_range_times:
        mn *= float(m_range_times.group(1))
        mx *= float(m_range_times.group(2))
    elif m_single_times:
        t = float(m_single_times.group(1))
        mn *= t
        mx *= t

    return {
        "min": mn * mult,
        "max": mx * mult,
        "unit": unit or "unknown",
        "freq": freq,
        "raw": text[:120],
    }


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    result = {}
    unparsed = []

    for c in d:
        cid = c["id"]
        dosage = c.get("dosage") or ""
        parsed = parse_dosage(dosage)
        if parsed:
            result[cid] = parsed
        else:
            unparsed.append((cid, dosage))

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"[OK] {OUT}")
    print(f"[OK] Распарсено: {len(result)}/{len(d)}")

    if unparsed:
        print(f"\n⚠️ Не распарсено: {len(unparsed)}")
        for cid, dos in unparsed:
            print(f"  {cid:25s} {dos[:80]}")

    # Примеры
    print("\n=== Примеры (первые 10) ===")
    for i, (cid, p) in enumerate(list(result.items())[:10]):
        print(f"  {cid:25s} {p['min']:>8}-{p['max']:<8} {p['unit']:6s} {p['freq']}")


if __name__ == "__main__":
    main()