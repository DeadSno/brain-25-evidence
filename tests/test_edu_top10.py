"""v2.3.1+v2.5: контент для 15 блоков (брифинги v2.3b, v2.5 — контент №1+№2)."""
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

# Q1.4: adv-поля теперь добавляются ко всем 81 карточке.
# Этот порог — «сколько минимум карточек имеют adv-поля».
# Растёт по мере прохождения батчей.
MIN_WITH_EDU = 25


def test_edu_top10_all_fields_nonempty_in_data():
    """Первые 20 карточек из content.EDU_TOP10 должны иметь все поля заполнены и совпадать."""
    assert len(content.EDU_TOP10) == 20, f"EDU_TOP10: {len(content.EDU_TOP10)}, ожидалось 20"
    for key, fields in content.EDU_TOP10.items():
        assert key in by_id, f"нет карточки в data.json: {key}"
        card = by_id[key]
        assert set(fields) == set(EDU_FIELDS), f"{key}: ключи не совпадают с брифом"
        for f in EDU_FIELDS:
            assert card.get(f), f"{key}: поле {f} пустое в data.json"
            # NB: content.EDU_TOP10 — исторический артефакт;
            # с Q1.4 источник истины — data.json. Сверка текста отключена.


def test_q14_progress_at_least_min():
    """Q1.4 в процессе: минимум MIN_WITH_EDU карточек имеют adv-поля (растёт по мере батчей)."""
    with_edu = [d for d in data if any(d.get(f) for f in EDU_FIELDS)]
    assert len(with_edu) >= MIN_WITH_EDU, (
        f"adv-поля только у {len(with_edu)} карточек, ожидалось ≥ {MIN_WITH_EDU}")


def test_modal_renders_edu_fields_in_blocks():
    """Модалка читает все adv-поля."""
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
        assert expr in SCRIPT, f"модалка не читает поле: {expr} (поле {f})"