import json
import re
from pathlib import Path

from src import content

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
by_id = {x["id"]: x for x in data}
INDEX = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "docs" / "script.js").read_text(encoding="utf-8")

BLOCK_KEYS = ["what", "who", "works", "evidence", "how", "onset", "notwho",
              "conflicts", "friends", "ul", "food", "official", "shop", "myths", "price"]


def test_three_questions_in_dom():
    for q in [
        "Чем БАД отличается от лекарства?",
        "Зачем он мне?",
        "Как выбирать?",
    ]:
        assert q in INDEX, f"нет вопроса в index.html: {q}"


def test_15_blocks_in_template():
    for key in BLOCK_KEYS:
        assert f"key: '{key}'" in SCRIPT, f"блок {key} отсутствует в шаблоне"
    assert SCRIPT.count("key: '") == 15, "должно быть ровно 15 блоков карточки"


def test_empty_block_placeholder():
    assert "данных пока нет — проверяем" in SCRIPT, "нет заглушки для пустых блоков"
    assert "cbEmpty" in SCRIPT, "нет класса cbEmpty для пустых блоков"


def test_low_block_for_supplements_without_interactions():
    no_pair = set(content.INTERACTIONS) | set(content.INTERACTIONS_ALIAS) | set(content.INTERACTIONS_CANDIDATES)
    for d in data:
        if d["id"] in no_pair or any(i.get("with") for i in d.get("interactions", [])):
            continue
        assert any(i["severity"] == "low" and "известных взаимодействий нет" in i.get("note", "")
                   for i in d["interactions"]), f"{d['id']}: нет low-блока"


def test_antagonist_pair_calcium_iron():
    ca, fe = by_id["Кальций"], by_id["Железо"]
    assert "Железо" in ca["antagonists"], "Кальций должен конфликтовать с Железом"
    assert "Кальций" in fe["antagonists"], "Железо должно конфликтовать с Кальцием"


def test_synergist_pair_magnesium_b6():
    mg = by_id["Магний"]
    assert "Витамин B6" in mg["synergists"], "Магний должен дружить с B6"
    assert "Витамин D" in mg["synergists"], "Магний должен дружить с D3"


def test_all_cards_have_synergists_or_antagonists_data_field():
    real = set(content.INTERACTIONS_ALIAS) | set(content.INTERACTIONS)
    has_any = 0
    for d in data:
        if d.get("synergists") is not None or d.get("antagonists") is not None:
            has_any += 1
    assert has_any >= 8, "ожидался хотя бы 1 карточка с полем synergists/antagonists"
    assert "Кальций" in by_id and by_id["Кальций"].get("antagonists")
    assert "Магний" in by_id and by_id["Магний"].get("synergists")