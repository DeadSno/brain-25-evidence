import pathlib, re

p = pathlib.Path('README.md')
text = p.read_text(encoding='utf-8')

# 1. Обновить бейдж version v2.0 → v3.1.0
text = re.sub(
    r'version-v2\.0-blue',
    'version-v3.1.0-blue',
    text
)

# 2. Обновить бейдж tests (было 24 passed)
text = re.sub(
    r'tests-24%20passed-brightgreen',
    'tests-122%20passed-brightgreen',
    text
)

# 3. Вставить секцию аудита после оглавления (перед первым ##)
audit_section = """

## 🎯 Аудит v3.0 (сентябрь 2026)

**81/81 добавка верифицирована** по методологии PRISMA:

| Грейд | Значение | Количество |
|-------|----------|------------|
| **A** | работает отлично | 8 (9.9%) |
| **B** | работает | 35 (43.2%) |
| **C** | зависит от контекста | 26 (32.1%) |
| **D** | не подтверждено | 12 (14.8%) |

**Результаты аудита:**
- 14 коммитов, 81 карточка в `data/processed/audit/`
- 2 тега релиза: `v3.0-audit-top20` (топ-20), `v3.0-audit-complete` (все 81)
- Методология: [methodology.html](docs/methodology.html)
- Скрипты прогона: `scripts/fetch_meta.py`, `scripts/integrate_audit.py`

---
"""

# ищем первый ## после оглавления (обычно "## Что это и зачем")
m = re.search(r'\n## ', text)
if m:
    text = text[:m.start()] + audit_section + text[m.start():]

p.write_text(text, encoding='utf-8')
print('README.md: бейдж v3.1.0 + секция аудита')
