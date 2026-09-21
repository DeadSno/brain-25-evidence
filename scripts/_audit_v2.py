"""Аудит v2 — механические проверки 51 карточки.

Нормы длин (из брифа) + возраст PMID + наличие evidence-файла.
Семантическую сверку с abstracts (факт подтверждается) — только для спорных.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
EVIDENCE = ROOT / "reports" / "evidence"

# 51 карточка из брифа
CARDS = [
    "B12","L-Теанин","Ежовик","Фосфатидилсерин","Alpha-GPC","CDP-холин",
    "Гуперзин А","Ресвератрол","Тирозин","Таурин","CoQ10","Пикногенол",
    "Готу кола","Валериана","Бета-аланин","L-цитруллин","Бузина","Зверобой",
    "5-HTP","Триптофан","Глюкозамин + хондроитин","Биотин","Гиалуроновая кислота",
    "Клюква","Пустырник","Боярышник","Бета-глюканы овса","Рибофлавин",
    "Лютеин + зеаксантин","Инозитол","Альфа-липоевая кислота","D-манноза",
    "Мака","Хром","Астаксантин","Расторопша","Лактоферрин","SAMe","Йохимбин",
    "Пажитник","Чёрный тмин","Трибулус","NMN","Кордицепс","Рейши","Хлорофилл",
    "Сывороточный протеин","Глутамин","Босвеллия","Витамин K2","Кверцетин",
]

NORMS = {
    "about": (51, 101), "who_needs": (57, 127), "onset": (40, 89),
    "myths": (85, 145), "food_sources": (35, 106),
    "guidelines": (58, 121), "how_to_choose": (49, 109),
}
FIELDS = list(NORMS.keys())
CUR_YEAR = 2026

by_id = {c["id"]: c for c in DATA}

# Найти evidence-файл (учитывая _ vs пробел)
def find_evidence(cid):
    for name in [cid, cid.replace(" ", "_"), cid.replace("_", " "),
                 cid.replace("+", "_").replace(" ", "_").strip("_")]:
        p = EVIDENCE / f"{name}.md"
        if p.exists():
            return p
    # fuzzy — по частичному совпадению
    normalized = re.sub(r"[^\w]", "", cid.lower())
    for p in EVIDENCE.glob("*.md"):
        if re.sub(r"[^\w]", "", p.stem.lower()) == normalized:
            return p
    return None

report = []
report.append("# Аудит v2 — 51 карточка (механическая проверка)\n")
report.append("Авто-скрипт: нормы длин + возраст PMID + наличие evidence.\n")
report.append("---\n")

issues_critical = []
issues_important = []
issues_cosmetic = []
ok_cards = []

for cid in CARDS:
    c = by_id.get(cid)
    if not c:
        report.append(f"## {cid}\n**❌ карточка не найдена в data.json**\n")
        issues_critical.append(f"{cid}: нет карточки")
        continue

    card_issues = []
    rows = []

    # 1. Нормы длин
    for f in FIELDS:
        v = c.get(f) or ""
        if not v:
            rows.append(f"| {f} | ❌ | пусто |")
            card_issues.append(("critical", f"{f}: пусто"))
            continue
        lo, hi = NORMS[f]
        n = len(v)
        if lo <= n <= hi:
            rows.append(f"| {f} | ✅ | {n} симв |")
        else:
            rows.append(f"| {f} | ⚠ важно | {n} симв (норма {lo}–{hi}) |")
            card_issues.append(("important", f"{f}: длина {n} вне нормы"))

    # 2. Возраст PMID в key_sources
    old_pmids = []
    for ks in (c.get("key_sources") or []):
        year = ks.get("year") or 0
        if isinstance(year, int) and CUR_YEAR - year > 5:
            old_pmids.append(f"{ks.get('pmid')} ({year})")
    if old_pmids:
        rows.append(f"| key_sources | ⚙ косметика | устаревшие: {', '.join(old_pmids)} |")
        card_issues.append(("cosmetic", f"старые PMID: {old_pmids}"))

    # 3. Evidence-файл
    ev = find_evidence(cid)
    if not ev:
        rows.append(f"| evidence | ⚠ важно | файл не найден |")
        card_issues.append(("important", "нет evidence-файла"))

    # Сводка по карточке
    if not card_issues:
        ok_cards.append(cid)
        report.append(f"## {cid} — **валидно**\n")
    else:
        cnt = {"critical": 0, "important": 0, "cosmetic": 0}
        for lvl, _ in card_issues:
            cnt[lvl] += 1
        parts = []
        if cnt["critical"]: parts.append(f"{cnt['critical']} критично")
        if cnt["important"]: parts.append(f"{cnt['important']} важно")
        if cnt["cosmetic"]: parts.append(f"{cnt['cosmetic']} косметика")
        report.append(f"## {cid} — проблема ({', '.join(parts)})\n")
        report.append("| Поле | Статус | Комментарий |")
        report.append("|---|---|---|")
        report.extend(rows)
        report.append("")

        for lvl, msg in card_issues:
            if lvl == "critical": issues_critical.append(f"{cid}: {msg}")
            elif lvl == "important": issues_important.append(f"{cid}: {msg}")
            else: issues_cosmetic.append(f"{cid}: {msg}")

# Сводка
report.append("\n---\n## Сводка\n")
report.append(f"- Проверено: {len(CARDS)} / {len(CARDS)}")
report.append(f"- Полей проверено: {len(CARDS) * 7}")
report.append(f"- Критично: **{len(issues_critical)}**")
report.append(f"- Важно: **{len(issues_important)}**")
report.append(f"- Косметика: **{len(issues_cosmetic)}**")
report.append(f"- Полностью валидных: **{len(ok_cards)}** ({', '.join(ok_cards[:10])}{'…' if len(ok_cards) > 10 else ''})\n")

OUT = ROOT / "reports" / "q14_audit_v2.md"
OUT.write_text("\n".join(report), encoding="utf-8")

print(f"[OK] {OUT}")
print(f"\nКритично: {len(issues_critical)}")
for x in issues_critical[:5]: print(f"  ❌ {x}")
print(f"\nВажно: {len(issues_important)}")
for x in issues_important[:5]: print(f"  ⚠️ {x}")
print(f"\nКосметика: {len(issues_cosmetic)}")
for x in issues_cosmetic[:5]: print(f"  ⚙ {x}")
print(f"\nВалидных карточек: {len(ok_cards)}/{len(CARDS)}")