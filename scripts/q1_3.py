"""Q1.3: Обновление радара профиля — честные оси.

Заменяет 2 "обманные" оси на честные:
  - Спрос (reviews)     -> Верифицированность (грейд + key_sources)
  - Интерес (trends)    -> Полнота карточки (база 40% + премиум 60%)

Мотивация (по ТЗ проекта "максимальная честность данных"):
  - reviews (WB)    - метрика продаж, а не качества доказательств
  - trends (Google) - интерес, а не научная ценность

Использование:
    python scripts/q1_3.py --dry-run   # только проверки
    python scripts/q1_3.py             # записать файл
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_JS = ROOT / "docs" / "script.js"
DATA_JSON = ROOT / "docs" / "data.json"


NEW_BLOCK = """  const BASE_FOR_PCT = supplements;   // нормировка по всей базе 81
  const prof = s => {
    // Ось 1: Наука — перцентиль по базе
    const science = pctile(s.scienceIndex || 0, BASE_FOR_PCT.map(x => x.scienceIndex));
    // Ось 2: База МА — перцентиль по базе
    const maBase = pctile(s.metaCount || 0, BASE_FOR_PCT.map(x => x.metaCount));

    // Ось 3: Верифицированность (грейд + бонус за key_sources)
    const gradeMap = { A: 80, B: 60, C: 40, D: 20 };
    const srcBonus = Math.min((s.key_sources || []).length, 5) * 4;
    const verified = Math.min((gradeMap[s.grade] || 0) + srcBonus, 100);

    // Ось 4: Полнота карточки (база 40% + премиум 60%)
    const baseFields = ['verdict', 'effects', 'dosage', 'course', 'caution'];
    const advFields = ['about', 'who_needs', 'onset', 'myths',
                       'food_sources', 'guidelines', 'how_to_choose'];
    const baseFilled = baseFields.filter(f => {
      const v = s[f];
      return Array.isArray(v) ? v.length > 0 : !!v;
    }).length;
    const advFilled = advFields.filter(f => {
      const v = s[f];
      return Array.isArray(v) ? v.length > 0 : (typeof v === 'string' && v.length > 0);
    }).length;
    const completeness = Math.round(
      (baseFilled / baseFields.length) * 40 +
      (advFilled / advFields.length) * 60
    );

    return [science, maBase, verified, completeness];
  };
  const PROF_LABELS = ['Наука', 'База МА', 'Верифицированность', 'Полнота карточки'];
"""

OLD_TOOLTIP = """              const raw = rawVals(s)[ctx.dataIndex];
              return ' ' + s.name + ' · ' + PROF_LABELS[ctx.dataIndex] + ': ' +
                Math.round(ctx.parsed.r) + '/100' +
                (raw != null ? ' · сырое: ' + (raw.toLocaleString ? raw.toLocaleString('ru-RU') : raw) : '');"""

NEW_TOOLTIP = """              return ' ' + s.name + ' · ' + PROF_LABELS[ctx.dataIndex] + ': ' +
                Math.round(ctx.parsed.r) + '/100';"""

LABELS_RE = re.compile(
    r"      labels: PROF_LABELS\.map\(l => l \+ ' \([^)]+\)'\),"
)

NEW_LABELS = """      labels: [
        'Наука (перцентиль по базе)',
        'База МА (перцентиль по базе)',
        'Верифицированность (0-100)',
        'Полнота карточки (0-100)'
      ],"""


def validate_data(data: list[dict]) -> None:
    """Проверки данных перед патчем."""
    assert len(data) == 81, f"Ожидаем 81 БАД, получено {len(data)}"
    for s in data:
        sid = s.get("id", "?")
        assert s.get("grade") in {"A", "B", "C", "D"}, (
            f"{sid}: недопустимый grade={s.get('grade')!r}"
        )
    print(f"[OK] Данные валидны: {len(data)} БАДов, у всех есть grade")


def patch_script_js(dry_run: bool = False) -> None:
    """Патч script.js: prof() + PROF_LABELS + labels + tooltip."""
    text = SCRIPT_JS.read_text(encoding="utf-8")
    original = text

    # Идемпотентность: уже пропатчено?
    if "rawVals" not in text and "Полнота карточки" in text:
        print("[SKIP] Патч уже применён — нечего делать.")
        return

    # 1. Блок: BASE_FOR_PCT + rawVals + prof + PROF_LABELS
    block_re = re.compile(
        r"  const BASE_FOR_PCT = supplements;[^\n]*\n"
        r"  const rawVals = s => \[[\s\S]*?\n  \];\n"
        r"  const prof = s => \{[\s\S]*?\n  \};\n"
        r"  const PROF_LABELS = \[[^\]]+\];\n",
        re.MULTILINE,
    )
    n = len(block_re.findall(text))
    if n == 0:
        raise RuntimeError(
            "Не найден блок BASE_FOR_PCT + rawVals + prof + PROF_LABELS. "
            "Проверь script.js вручную."
        )
    assert n == 1, f"Найдено {n} совпадений блока — ожидалось 1"
    text = block_re.sub(NEW_BLOCK, text, count=1)
    print("[OK] Блок prof() + PROF_LABELS заменён на 4 честные оси")

    # 2. labels в options радара
    if LABELS_RE.search(text):
        text = LABELS_RE.sub(NEW_LABELS, text, count=1)
        print("[OK] labels в radar options обновлены")
    else:
        print("[SKIP] labels в radar options уже обновлены")

    # 3. Tooltip callback — убираем обращение к rawVals
    if OLD_TOOLTIP in text:
        text = text.replace(OLD_TOOLTIP, NEW_TOOLTIP, 1)
        print("[OK] Tooltip callback обновлён")
    else:
        print("[WARN] Tooltip callback не найден по шаблону — проверь вручную")

    # 4. Финальные проверки
    if "rawVals" in text:
        remaining = [
            f"  {i + 1}: {line.strip()}"
            for i, line in enumerate(text.splitlines())
            if "rawVals" in line
        ]
        print(f"[WARN] rawVals ещё встречается ({len(remaining)} мест):")
        for r in remaining[:5]:
            print("       " + r)
    else:
        print("[OK] rawVals полностью удалён")

    if "Полнотакарточки" in text:
        text = text.replace("Полнотакарточки", "Полнота карточки")
        print("[FIX] Опечатка «Полнотакарточки» исправлена")

    if dry_run:
        print("\n[DRY-RUN] Файл НЕ записан. Убери --dry-run, чтобы применить.")
        return

    if text == original:
        print("\n[SKIP] Изменений нет.")
        return

    SCRIPT_JS.write_text(text, encoding="utf-8")
    print(f"\n[OK] Файл записан: {SCRIPT_JS}")


def main() -> int:
    """CLI-точка входа."""
    parser = argparse.ArgumentParser(description="Q1.3: честные оси радара")
    parser.add_argument("--dry-run", action="store_true", help="только проверки")
    args = parser.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    validate_data(data)
    patch_script_js(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())