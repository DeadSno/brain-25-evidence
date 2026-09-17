import pathlib, re
from datetime import date

p = pathlib.Path('CHANGELOG.md')
text = p.read_text(encoding='utf-8')

section = """## [v3.1.0] — 2026-09-17
### 🎯 Полный аудит 81 добавки (v3.0) + чистка сайта (v3.1)

**Аудит v3.0** — ручная верификация 81 добавки по методологии PRISMA:
- 14 коммитов аудита, 2 тега релиза (`v3.0-audit-top20`, `v3.0-audit-complete`)
- 81 карточка аудита в `data/processed/audit/` (PRISMA-воронка + грейды A-D)
- Грейды интегрированы в `docs/data.json`, бейджи A/B/C/D рендерятся на сайте
- Распределение: A=8, B=35, C=26, D=12 (честная картина доказательности)

**Чистка v3.1** — docs/ теперь только сайт, без внутренних документов:
- Удалено 33 устаревших файла (drafts/briefs/reports/archived/duplicates)
- 4 внутренних MD перенесены в корень (STATE/MASTER_RUNBOOK/ROADMAP/approve_queue)
- Удалены: дубль `serve.py`, пустой `data_price_history.json`, архивный CI-конфиг
- Починены битые ссылки на удалённые `changelog_public.html` / `for_doctors.html`
- Палитра грейдов: зелёный / лайм / янтарь / красный (бейджи + вердикты + точки)
- Поле `code` у 81/81 добавок (числа 1/0/-1, вердикты красятся)

**Документация:**
- `methodology.html` переписан: PRISMA-воронка, грейды, 81 карточка
- `faq.html` дополнен: 4 вопроса про аудит и грейды

Скрипты прогона аудита: `scripts/fetch_meta.py`, `scripts/fetch_meta_subset.py`, `scripts/integrate_audit.py`

"""

# вставляем сразу после # Changelog (если есть) или в начало
if text.startswith('# '):
    idx = text.find('\n') + 1
    while idx < len(text) and text[idx] in '\n\r ':
        idx += 1
    text = text[:idx] + '\n' + section + text[idx:]
else:
    text = section + text

p.write_text(text, encoding='utf-8')
print('CHANGELOG.md: секция v3.1.0 добавлена')
