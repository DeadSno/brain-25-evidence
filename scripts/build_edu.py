"""Сборка контента топ-10 для 15 блоков в docs/data.json из src/content.py (v2.3.1).

Читает EDU_TOP10 из content.py, прокидывает 8 текстовых полей
(about/who_needs/onset/upper_limit/food_sources/guidelines/how_to_choose/myths)
в карточки data.json по каноничному id. Поля g/key_sources не трогаются (цикл 4).

v2.6 добавляет служебные поля всех карточек:
- year_last_ma: год последнего мета-анализа = max(year) по key_sources, иначе null (C2)
- updated: дата последнего коммита docs/data.json (git log) для бейджа «Обновлено» (D1)
- price_source: nullable заглушка под иконку источника цены (F1) — не выдумываем
  источники, бот update_prices.py заполнит при живом прогоне

Запуск:
    python scripts/build_edu.py
Идемпотентно: перезапуск не дублирует поля (поле есть — пропуск).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import content

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

EDU_FIELDS = ["about", "who_needs", "onset", "upper_limit",
              "food_sources", "guidelines", "how_to_choose", "myths"]


def last_commit_date(rel_path: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel_path],
            capture_output=True, text=True, cwd=str(ROOT), check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in data}

    attached = 0
    skipped = 0
    missing = []
    for key, fields in content.EDU_TOP10.items():
        if key not in by_id:
            missing.append(key)
            continue
        card = by_id[key]
        if all(card.get(f) == v for f, v in fields.items()):
            skipped += 1
            continue
        card.update(fields)
        attached += 1

    print(f"edu attached: {attached} cards (skipped: {skipped})")
    if missing:
        print(f"WARNING: нет карточек для id: {missing}")

    # v2.6: служебные поля всех карточек
    updated = last_commit_date("docs/data.json") or "2026-09-14"
    ylm_changed = updated_changed = ps_added = 0
    for card in data:
        ks_years = [s.get("year") for s in (card.get("key_sources") or []) if s.get("year")]
        want_ylm = max(ks_years) if ks_years else None
        if "year_last_ma" not in card or card.get("year_last_ma") != want_ylm:
            card["year_last_ma"] = want_ylm
            ylm_changed += 1
        if card.get("updated") != updated:
            card["updated"] = updated
            updated_changed += 1
        if "price_source" not in card:
            card["price_source"] = None
            ps_added += 1

    print(f"year_last_ma updated: {ylm_changed}; updated set: {updated_changed}; price_source added: {ps_added}")

    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print("data.json updated")


if __name__ == "__main__":
    main()