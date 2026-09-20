"""Финальный проход README: WB + заголовок + корреляции."""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
text = README.read_text(encoding="utf-8")
original = text

# ── 1. Заголовок: цена vs наука → доказательства и механизмы ──
text = text.replace(
    "# БАДы: цена vs наука\n",
    "# БАДы: доказательства и механизмы\n"
)
text = text.replace(
    "![Превью: пузырьковая диаграмма цена vs наука](docs/og.png)",
    "![Превью дашборда](docs/og.png)"
)

# ── 2. Оглавление: убрать п.8 «Автообновление цен», сдвинуть ──
text = text.replace("8. [Автообновление цен](#автообновление-цен)\n", "")
for old, new in [
    ("9. [Roadmap]", "8. [Roadmap]"),
    ("10. [Как помочь проекту]", "9. [Как помочь проекту]"),
    ("11. [Дисклеймер и лицензия]", "10. [Дисклеймер и лицензия]"),
]:
    text = text.replace(old, new)

# ── 3. Блок корреляций: убрать строки про Цену и WB, оставить Wikipedia ──
text = text.replace(
    "| Наука x Цена | **-0.34** | 24 | Дорогие добавки **не** научнее дешёвых |\n", ""
)
text = text.replace(
    "| Наука x Отзывы WB | -0.17 | 25 | Самые покупаемые — не самые обоснованные |\n", ""
)
text = text.replace(
    "| Google Trends x WB | -0.01 | 25 | Ищут **не то**, что покупают |\n", ""
)
# Заголовок блока корректируем
text = text.replace(
    "### Корреляции (наука x рынок)",
    "### Корреляции (наука x интерес)"
)

# ── 4. Таблица «Данные»: убрать строку Цен ──
text = text.replace("| Цен | 55 из 81 (Wildberries, 70+ товаров) |\n", "")

# ── 5. Структура репо: убрать collect_prices + дубль map.html ──
text = text.replace(
    "│   ├── map.html                   # карта механизмов v4 (81 узел)\n", ""
)
text = text.replace(
    "│   └── collect_prices.py          # ежедневный сбор цен WB\n", ""
)
text = text.replace(
    "    ├── workflows/collect_prices.yml  # cron 06:00 МСК (бот цен)\n", ""
)
text = text.replace(
    "    └── ISSUE_TEMPLATE/data-error.md  # шаблон сообщений об ошибках",
    "    └── ISSUE_TEMPLATE/data-error.md  # шаблон сообщений об ошибках"
)

# ── 6. Дисклеймер: убрать строку про цены ──
text = text.replace(
    "- Цены маркетплейсов меняются ежедневно; сайт обновляется раз в сутки\n", ""
)

# ── 7. Таблица источников: убрать Цены и Популярность ──
text = text.replace("| Цены | Wildberries (поиск, медиана по товарам) |\n", "")
text = text.replace("| Популярность | Google Trends, Wikipedia pageviews |\n", "")

# ── Применяем ──
if text == original:
    print("[SKIP] Изменений нет.")
    raise SystemExit(0)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(README, README.with_suffix(f".md.bak-{ts}"))
README.write_text(text, encoding="utf-8")

print("[OK] Правки применены")
print(f"[OK] Бэкап: README.md.bak-{ts}")

# ── Проверка остатков ──
rest = []
for i, line in enumerate(text.split("\n"), 1):
    if "Wildberries" in line or " WB " in line or "цена vs наука" in line:
        rest.append(f"  {i}: {line.strip()[:80]}")
if rest:
    print("\n⚠️ Остатки WB/цен:")
    for r in rest:
        print(r)
else:
    print("\n✅ WB/цены полностью удалены")