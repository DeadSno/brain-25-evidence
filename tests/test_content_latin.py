"""v2.3.2: латинские буквы внутри кириллических слов = FAIL (guard).
Латиница в терминах/именах собственных (EPA, DHA, NF-κB, TOTOX, LGG, Creapure и
аналоги) — разрешена через белый список ТОКЕНОВ (окружений), не слов целиком.
Проверяем все текстовые поля data.json и все строковые значения content.py.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import content

ROOT = Path(__file__).resolve().parents[1]

CYRILLIC = range(0x0400, 0x0500)

# Смешение скриптов: латинская буква (ASCII a-zA-Z) прямо у кириллицы − подозрение.
MIXED = re.compile(r"(?<=[А-Яа-яЁё])([A-Za-z])|([A-Za-z])(?=[А-Яа-яЁё])")

# Белый список: латинские знак-окружения, признанные терминами/именами.
# Сравнение ПО ОБРАЗУЮЩЕМУ СЛОВУ (кириллическая часть игнорируется через spacer).
WHITELIST = {
    # термины/имена собственные (выписаны явно после прогона сканера)
    "NF-κB", "DHA", "EPA", "TOTOX", "LGG", "Creapure", "KSM-66", "EGb761",
    "SMD", "Hedges' g", "Cohen's d", "CONTRA", "k", "K", "CT", "MRI",
    "Alpha-GPC", "CDP-холин", "B12-дефицит", "25(OH)D", "D3",
}


def iter_values() -> list[tuple[str, str]]:
    """Все текстовые строки: data.json (все поля) + content.py (строковые значения)."""
    out: list[tuple[str, str]] = []
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    for card in data:
        for k, v in card.items():
            if isinstance(v, str):
                out.append((f"data.json[{card['id']}].{k}", v))

    def walk(o, path):
        if isinstance(o, str):
            out.append((path, o))
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    walk(vars(content), "content.py")
    return out


def mixed_fragments(text: str) -> list[str]:
    """Фрагменты 'латиница-у-кириллицы' + слово, в котором это произошло."""
    words = re.split(r"([^А-Яа-яЁёA-Za-z]+)", text)
    hits: set[str] = set()
    for w in words:
        if not any(ch in w for ch in "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"):
            continue
        if not MIXED.search(w):
            continue
        norm = w.strip("()[]{}\"'«»,.!?:;-")
        for item in WHITELIST:
            norm = norm.replace(item, "")
        if not MIXED.search(norm):
            continue
        hits.add(w)
    return sorted(hits)


def test_no_latin_inside_cyrillic_words():
    bad: list[tuple[str, str, list[str]]] = []
    for path, text in iter_values():
        frags = mixed_fragments(text)
        if frags:
            bad.append((path, text[:90], frags))
    assert not bad, f"латиница внутри кириллических слов ({len(bad)} мест):\n" + "\n".join(
        f"- {p}: {f} <- {t}" for p, t, f in bad[:25])


def test_whitelist_terms_still_present():
    """Значимые латинские термины не должны потеряться при чистке."""
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    blob = json.dumps(data, ensure_ascii=False)
    assert "EPA+DHA" in blob or "EPA/DHA" in blob
    assert "TOTOX" in blob