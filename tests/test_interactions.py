import json
from pathlib import Path

from src import content

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
SEVERITIES = ["critical", "high", "medium", "low"]


def test_interactions_schema():
    for s in data:
        if "interactions" not in s:
            continue
        assert isinstance(s["interactions"], list), f"{s['id']}: interactions не список"
        for inter in s["interactions"]:
            assert "with" in inter, f"{s['id']}: нет поля with"
            assert inter["severity"] in SEVERITIES, f"{s['id']}: странный severity {inter['severity']}"
            assert "note" in inter, f"{s['id']}: нет поля note"


def test_critical_interactions_documented():
    critical = ["Зверобой", "5-HTP", "Йохимбин", "Тирозин", "Фенилаланин", "Триптофан"]
    present = [sid for sid in critical if any(x["id"] == sid for x in data)]
    for sid in present:
        s = next(x for x in data if x["id"] == sid)
        assert "interactions" in s, f"{sid}: нет interactions"
        assert any(i["severity"] == "critical" for i in s["interactions"]), \
            f"{sid}: нет критических взаимодействий"


def test_interactions_keys_resolve():
    ids = {x["id"] for x in data}
    for key in content.INTERACTIONS:
        if key in ids:
            continue
        if key in content.INTERACTIONS_CANDIDATES:
            continue
        target = content.INTERACTIONS_ALIAS.get(key)
        assert target and target in ids, \
            f"ключ INTERACTIONS не резолвится: {key!r} (нет ни id, ни алиаса, ни кандидата)"
    for alias, target in content.INTERACTIONS_ALIAS.items():
        assert target in ids, f"алиас {alias!r} → {target!r}: цели нет в data.json"
    for cand in content.INTERACTIONS_CANDIDATES:
        assert cand in ids or cand in content.INTERACTIONS, \
            f"кандидат {cand!r} нет ни в data.json, ни в INTERACTIONS"


def test_all_interactions_attached():
    by_id = {x["id"]: x for x in data}
    for key, items in content.INTERACTIONS.items():
        target = content.INTERACTIONS_ALIAS.get(key, key)
        if target not in by_id:
            continue
        card = by_id[target]
        assert "interactions" in card, f"{target}: словарь есть, поле не пришло в data.json"
        assert any(i["note"] == it["note"] and i["with"] == it["with"]
                   for it in items for i in card["interactions"]), \
            f"{target}: данные в data.json не совпадают со словарём"