"""Гейт свежести `docs/data_index.json` относительно `docs/data.json`.

Зачем отдельный тест, если есть `tests/test_index_sync.py`
----------------------------------------------------------
`test_index_sync.py` запускает `build_index.py --check` и сверяет **проекцию**
(`supplements` == `INDEX_FIELDS`-выборка из `data.json`). Этого достаточно,
пока меняются значения полей, но недостаточно для находки DATA-01: индекс
может отставать по служебным маркерам (`_meta.source_sha256_16`,
`_meta.generated_at`, `_meta.count`, `_meta.fields`), оставаясь при этом
построчно идентичным. Именно так DATA-01 и прожила до FIX-41: `--check`
был зелёным, а `_meta` врала о происхождении данных.

Проверки здесь — про метаданные источника, а не про содержимое карточек:

1. `_meta.source_sha256_16` совпадает с `sha256(data.json)[:16]`.
2. `_meta.count` == число карточек в `data.json`.
3. `_meta.generated_at` — валидный ISO-8601 с часовым поясом.
4. `_meta.fields` == `INDEX_FIELDS` из генератора (иначе расширение списка
   полей не доедет до индекса и никто этого не заметит).

Алгоритм хеша не дублируется: `sha256_of` импортируется из
`scripts/build_index.py` — источника истины. Если генератор поменяет
нормализацию, тест поедет вместе с ним.

Фикс при падении: `python scripts/build_index.py`.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_index as bi  # noqa: E402

HINT = "data_index.json устарел, запусти: python scripts/build_index.py"


def _data_text() -> str:
    return (ROOT / "docs" / "data.json").read_text(encoding="utf-8")


def _index_payload() -> dict:
    path = ROOT / "docs" / "data_index.json"
    assert path.exists(), f"{path} не найден. {HINT}"
    return json.loads(path.read_text(encoding="utf-8"))


def freshness_problems(data_text: str, index_payload: dict) -> list[str]:
    """Все расхождения `_meta` с фактическим `data.json`.

    Вынесено отдельной функцией, чтобы гейт можно было проверить на
    подделанном индексе, не трогая файл на диске.
    """
    meta = index_payload.get("_meta") or {}
    rows = json.loads(data_text)
    problems: list[str] = []

    expected = bi.sha256_of(data_text)
    actual = meta.get("source_sha256_16")
    if actual != expected:
        problems.append(
            f"source_sha256_16: в индексе {actual!r}, фактически {expected!r}"
        )

    if meta.get("count") != len(rows):
        problems.append(
            f"count: в индексе {meta.get('count')!r}, карточек в data.json {len(rows)}"
        )

    stamp = meta.get("generated_at")
    try:
        parsed = datetime.fromisoformat(stamp) if isinstance(stamp, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        problems.append(f"generated_at: {stamp!r} — не ISO-8601 с часовым поясом")

    if list(meta.get("fields") or []) != list(bi.INDEX_FIELDS):
        problems.append(
            f"fields: в индексе {len(meta.get('fields') or [])} полей, "
            f"в build_index.INDEX_FIELDS {len(bi.INDEX_FIELDS)}"
        )

    return problems


def test_data_index_meta_is_fresh():
    """Служебные маркеры индекса описывают текущий data.json."""
    problems = freshness_problems(_data_text(), _index_payload())
    assert not problems, (
        f"{HINT}\n  " + "\n  ".join(problems)
    )


def test_gate_detects_stale_sha():
    """Гейт обязан краснеть, если маркер источника подменён.

    Проверка самого гейта: без неё тест мог бы «проходить» и при полностью
    отключённой сверке. Индекс на диске не трогается — подмена живёт в
    памяти.
    """
    text = _data_text()
    payload = _index_payload()
    payload = json.loads(json.dumps(payload))  # копия, чтобы не менять кэш
    payload["_meta"]["source_sha256_16"] = "0000000000000000"

    problems = freshness_problems(text, payload)
    assert any("source_sha256_16" in p for p in problems), (
        "гейт не заметил подменённый source_sha256_16 — сверка не работает"
    )
