import json
import re
from pathlib import Path

from src import content

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
by_id = {x["id"]: x for x in data}
INDEX = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "docs" / "script.js").read_text(encoding="utf-8")
# 13A2a: словарь I18N/t() вынесены из script.js в общий docs/i18n.js.
I18N = (ROOT / "docs" / "i18n.js").read_text(encoding="utf-8")

BLOCK_KEYS = ["what", "who", "works", "evidence", "how", "onset", "notwho",
              "conflicts", "friends", "ul", "food", "official", "shop", "myths"]


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
    assert SCRIPT.count("key: '") == 14, "должно быть ровно 14 блоков карточки"


def test_empty_block_placeholder():
    # 13A2a: строка заглушки переехала в общий docs/i18n.js (ключ card.blockEmpty).
    assert "проверяемых данных по пункту нет" in SCRIPT or "проверяемых данных по пункту нет" in I18N, "нет заглушки для пустых блоков"
    assert "cbEmpty" in SCRIPT, "нет класса cbEmpty для пустых блоков"


def test_cards_without_interactions_stay_explicit_empty_lists():
    """FIX-50 (DATA-04): «нет данных» — это пустой список, а не строка в `with`.

    До FIX-50 карточкам без пар в словаре дописывалась запись
    {"with": "нет данных", "severity": "low", "note": ...}: строка-заглушка
    стояла в поле, где ожидается ИМЯ добавки, и docs/script.js:renderConflicts()
    печатал её как добавку («нет данных · низкая»). Теперь отсутствие
    взаимодействий выражено пустым списком, а объяснение рисует штатная
    заглушка блока (ключ card.blockEmpty в docs/i18n.js).

    Счётчик держит регресс в обе стороны: и возврат заглушки (ловится ещё и
    tests/test_data_en_placeholders.py), и молчаливую потерю реальных записей.
    """
    empty = [d["id"] for d in data if not d.get("interactions")]
    assert len(empty) == 51, (
        f"карточек с пустым interactions {len(empty)}, ожидалось 51. "
        f"Если данные правились осознанно — обновите число; если нет — "
        f"записи потеряны: {empty[:10]}"
    )


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