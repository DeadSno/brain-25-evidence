"""v2.3.1+v2.5: контент для 15 блоков (брифы v2.3b, v2.5 — контент №1+№2)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import content

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
by_id = {x["id"]: x for x in data}
SCRIPT = (ROOT / "docs" / "script.js").read_text(encoding="utf-8")

EDU_FIELDS = ["about", "who_needs", "onset", "upper_limit",
              "food_sources", "guidelines", "how_to_choose", "myths"]
EXPECTED = 20


def test_edu_top10_all_fields_nonempty_in_data():
    assert len(content.EDU_TOP10) == EXPECTED, f"EDU_TOP10: {len(content.EDU_TOP10)}, ожидалось {EXPECTED}"
    for key, fields in content.EDU_TOP10.items():
        assert key in by_id, f"нет карточки в data.json: {key}"
        card = by_id[key]
        assert set(fields) == set(EDU_FIELDS), f"{key}: ключи не совпадают с брифом"
        for f in EDU_FIELDS:
            assert card.get(f), f"{key}: поле {f} пустое в data.json"
            assert card[f] == fields[f], f"{key}: текст {f} разошёлся с EDU_TOP10 (редактура?!)"


def test_edu_top10_only_top10_fields_attached():
    with_edu = [d for d in data if any(f in d for f in EDU_FIELDS)]
    assert len(with_edu) == EXPECTED, (
        f"edu-поля у {len(with_edu)} карточек, ожидалось только у {EXPECTED}")


def test_modal_renders_edu_fields_in_blocks():
    mapping = {
        "about": "s.about",
        "who_needs": "s.who_needs",
        "onset": "s.onset",
        "upper_limit": "s.upper_limit",
        "food_sources": "s.food_sources",
        "guidelines": "s.guidelines",
        "how_to_choose": "s.how_to_choose",
        "myths": "s.myths",
    }
    for f, expr in mapping.items():
        assert expr in SCRIPT, f"модалка не читает новое поле: {expr} (поле {f})"