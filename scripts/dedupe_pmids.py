"""One-off очистка дублей PMID в docs/data.json (DATA-P2-16).

Проблема: 13 разных PMID встречаются в key_sources более чем одной карточки
(跨-карточные дубли). Внутри одной карточки дублей нет
(тест test_no_duplicate_pmids_within_card уже проходит).

Правило удаления (детерминированно, одна запись на дублированный PMID):
  * Для каждого PMID, встречающегося в более чем одной карточке, оставляем
    все вхождения кроме одного — удаляем запись из ПОСЛЕДНЕЙ не-курируемой
    карточки (самый высокий индекс карточки, которой нет в MANUAL_PMIDS).
  * Курируемые карточки (MANUAL_PMIDS, см. scripts/search_sources.py) никогда
    не трогаем, чтобы test_curated_pmids_match_data_json продолжал проходить:
    data.json для этих карточек должен совпадать с MANUAL_PMIDS.

Итог: ровно 13 записей удаляется (по одной на каждый из 13 дублированных PMID),
суммарное число key_sources уменьшается на 13 (393 -> 380).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"

# MANUAL_PMIDS — имена карточек (id == name), чьи key_sources нельзя менять.
sys.path.insert(0, str(ROOT / "scripts"))
from search_sources import MANUAL_PMIDS  # noqa: E402


def main() -> int:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    manual_names = set(MANUAL_PMIDS.keys())

    # pmid -> [(card_index, entry_index_in_key_sources), ...] в порядке data.json
    occ: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for ci, card in enumerate(data):
        for ei, src in enumerate(card.get("key_sources") or []):
            p = src.get("pmid")
            if p:
                occ[str(p)].append((ci, ei))

    before = sum(len(c.get("key_sources") or []) for c in data)
    victims: list[tuple[str, int, int, str]] = []  # (pmid, ci, ei, card_id)

    for pmid, positions in sorted(occ.items()):
        if len(positions) <= 1:
            continue  # не дублируется между карточками
        nonmanual = [
            pos for pos in positions if data[pos[0]]["id"] not in manual_names
        ]
        if not nonmanual:
            continue  # все вхождения на курируемых карточках — не трогаем
        # Удаляем последнее вхождение на не-курируемой карточке.
        ci, ei = nonmanual[-1]
        victims.append((pmid, ci, ei, data[ci]["id"]))

    # Удаляем сгруппированно по карточкам в обратном порядке индексов записи,
    # чтобы сдвиги не ломали позиции остальных victim'ов той же карточки.
    by_card: dict[int, list[tuple[int, str, str]]] = defaultdict(list)
    for pmid, ci, ei, cid in victims:
        by_card[ci].append((ei, pmid, cid))

    removed = 0
    removed_from: list[tuple[str, str]] = []
    for ci, entries in by_card.items():
        for ei, pmid, cid in sorted(entries, key=lambda x: x[0], reverse=True):
            del data[ci]["key_sources"][ei]
            removed += 1
            removed_from.append((pmid, cid))

    # Записываем в том же формате: 2 пробела, ensure_ascii=False, завершающий \n.
    DATA_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    after = sum(len(c.get("key_sources") or []) for c in data)
    print(f"key_sources before={before} after={after} removed={removed}")
    for pmid, cid in removed_from:
        print(f"  removed PMID {pmid} from card {cid}")
    assert before - after == removed, "count mismatch"
    assert removed == 13, f"ожидалось удалить 13 записей, удалено {removed}"
    return 0


if __name__ == "__main__":
    sys.exit(main())
