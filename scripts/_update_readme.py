"""Точечное обновление README.md под текущее состояние (v3.1, 20.09.2026).

Замены:
- badge tests 122 → 112
- удаление блоков Wildberries (цены, автообновление)
- добавление atlas / interactions в структуру и навигацию
- roadmap v3.1
- дата/версия в финале
- локальный запуск: 17 → 112 passed
"""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
text = README.read_text(encoding="utf-8")
original = text

# ── 1. Точечные замены ─────────────────────────────────────────
REPLACEMENTS = [
    ("badge: tests 122 → 112",
     "tests-122%20passed", "tests-112%20passed"),

    ("badge: version v3.1.0 → v3.1",
     "version-v3.1.0", "version-v3.1"),

    ("top bar: убрать WB",
     "> Вердикты по мета-анализам PubMed, цены за месяц с Wildberries, активные клинические испытания.",
     "> Вердикты по мета-анализам PubMed, механизмы, атлас, карта связей, активные клинические испытания."),

    ("навигация: добавить atlas + interactions",
     "[Открыть сайт](https://deadsno.github.io/brain-25-evidence/) | [Карта механизмов](https://deadsno.github.io/brain-25-evidence/map.html) | [Задать вопрос]",
     "[Открыть сайт](https://deadsno.github.io/brain-25-evidence/) | [Карта механизмов](https://deadsno.github.io/brain-25-evidence/map.html) | [Карта связей](https://deadsno.github.io/brain-25-evidence/interactions.html) | [Атлас](https://deadsno.github.io/brain-25-evidence/atlas.html) | [Задать вопрос]"),

    ("таблица: убрать строку Цена за месяц",
     "| Цена за месяц | Сколько реально платишь | Wildberries (медиана) |\n", ""),

    ("таблица: убрать строку Ценность",
     "| Ценность | Сколько науки за 100 руб. | Расчётная величина |\n", ""),

    ("структура: добавить atlas + interactions",
     "│   ├── map.html                   # карта механизмов v4 (81 узел)",
     "│   ├── map.html                   # карта механизмов (81 узел + оверлей + кросс-связи)\n│   ├── atlas.html                 # атлас: 25 хабов × 81 добавка\n│   ├── interactions.html          # карта связей (синергии/конфликты)"),

    ("локальный запуск: 17 → 112 passed",
     "# 3. Прогони тесты (должно быть 17 passed)",
     "# 3. Прогони тесты (должно быть 112 passed)"),

    ("финал: версия/дата",
     "Сделано с любопытством к доказательной медицине. v1.2, 09.09.2026.",
     "Сделано с любопытством к доказательной медицине. v3.1, 20.09.2026."),
]

# ── 2. Удаляемые блоки (по маркеру — от маркера до след. ## ) ──
DELETE_BLOCKS = [
    ("блок «Автообновление цен»", "## Автообновление цен"),
    ("блок «Ценность»", "### Ценность"),
]

# ── 3. Прочие удаления (строки) ────────────────────────────────
DELETE_LINES = [
    "| Цена | 55 из 81 (Wildberries, 70+ товаров) |",
    "**Почему у одной добавки нет цены (Ашваганда):**",
]

# ── 4. Новый Roadmap ────────────────────────────────────────────
NEW_ROADMAP = """## Roadmap

### v3.1 — ✅ текущая (20.09.2026)

- 81 добавка, adv-поля 81/81 (Q1.4 завершён)
- Hedges' g для 63/81 (59 с CI)
- Механизмы 81/81 (среднее 3.07)
- Атлас: 25 хабов × 81 добавка
- Карта связей: severity-фильтр, сайдбар, PNG
- Аудит данных: группы A/B/C/D закрыты
- PWA v31: установка на телефон, офлайн-режим
- Mobile-адаптив всех страниц

### v4.0 — план

- Калькулятор дозировок (достаточность / конфликты / синергии)
- Расширение базы до 100+ добавок
- Полное ревью кода + улучшения архитектуры
- CI/CD: автотесты на push через GitHub Actions
- PDF-экспорт карточек для врачей
- Sitemap + SEO-мета

"""

# ── Применяем замены ───────────────────────────────────────────
print("Точечные замены:")
for name, old, new in REPLACEMENTS:
    if old in text:
        text = text.replace(old, new, 1)
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} — не найдено")

print("\nУдаляемые блоки:")
for name, marker in DELETE_BLOCKS:
    pattern = re.compile(rf"^{re.escape(marker)}\n.*?(?=\n## |\n### |\Z)", re.DOTALL | re.MULTILINE)
    if pattern.search(text):
        text = pattern.sub("", text, count=1)
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} — не найдено")

print("\nУдаляемые строки:")
for line in DELETE_LINES:
    if line in text:
        # удаляем строку целиком + пустая строка после, если есть
        pattern = re.compile(rf"^{re.escape(line)}.*?$\n\n?", re.MULTILINE)
        text = pattern.sub("", text, count=1)
        print(f"  ✓ {line[:60]}…")
    else:
        print(f"  ✗ {line[:60]}… — не найдено")

print("\nRoadmap:")
roadmap_pattern = re.compile(r"^## Roadmap\n.*?(?=\n## |\Z)", re.DOTALL | re.MULTILINE)
if roadmap_pattern.search(text):
    text = roadmap_pattern.sub(NEW_ROADMAP, text, count=1)
    print("  ✓ Roadmap заменён")
else:
    print("  ✗ Roadmap — не найден (проверь вручную)")

# ── Сохраняем ──────────────────────────────────────────────────
if text == original:
    print("\n[SKIP] Изменений нет.")
    raise SystemExit(0)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = README.with_suffix(f".md.bak-{ts}")
shutil.copy2(README, backup)
README.write_text(text, encoding="utf-8")

print(f"\n[OK] Бэкап: {backup.name}")
print(f"[OK] Записано: {README}")