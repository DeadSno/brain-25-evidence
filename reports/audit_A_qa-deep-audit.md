# QA Deep Audit — Batch A, Skill 2/5

**Дата:** 2026-10-07
**Ветка:** v5.6-dev
**Коммит:** 11fea20
**Скилл:** qa-deep-audit

---

## 1. Сводка

| Метрика | Значение |
|---------|----------|
| Тестов собрано | 989 |
| Тестов пройдено | 790 |
| Тестов skipped | 2 |
| Тестов упало | 0 |
| Время прогона | 4.54s |
| Предупреждений | 1 (KNOWN_DEAD_CSS) |
| Скриптов в scripts/ | 89 |
| Скриптов без тестов | 73 |
| Критичных скриптов без тестов | 20 |

**Покрытие тестами:** 16 из 89 скриптов scripts/ имеют прямое упоминание в тестах (18%). 20 критичных скриптов без тестов.

---

## 2. P0 (критичные находки)

**P0 не найдены.**

---

## 3. P1 (важные находки)

### QA-P1-1: Критичные скрипты без тестов

**Файлы:** `scripts/build_api.py`, `scripts/build_key_sources.py`, `scripts/build_interactions.py`, `scripts/build_interactions_graph.py`, `scripts/check_state.py`, `scripts/validate_proposal.py`, `scripts/analyze_coi.py`, `scripts/build_sitemap.py`, `scripts/build_feed.py`, `scripts/build_edu.py`, `scripts/build_timeseries.py`, `scripts/build_ma_timeline.py`, `scripts/build_changelog_public.py`, `scripts/build_slim.py`, `scripts/apply_adv.py`, `scripts/apply_drafts.py`, `scripts/apply_mechs.py`, `scripts/sync_test_count.py`, `scripts/rebuild_index.py`, `scripts/recalc_science_index.py`, `scripts/update_all.py`

**Что не так:** 20 скриптов, которые влияют на данные или контент сайта, не имеют тестов. При рефакторинге или изменении легко сломать функциональность без обнаружения.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
test_content = ''
for f in Path('tests').glob('test_*.py'):
    test_content += f.read_text(encoding='utf-8')
critical = ['build_api', 'build_key_sources', 'build_interactions', 'check_state', 'validate_proposal', 'analyze_coi']
for c in critical:
    if c not in test_content:
        print(f'MISSING: {c}')
"
```

**Рекомендация:** Добавить тесты для скриптов, которые:
- Генерируют данные (build_api, build_key_sources, build_interactions)
- Валидируют данные (validate_proposal, validate_sources)
- Влияют на контент (build_feed, build_edu, build_sitemap)
- Считают метрики (check_state, sync_test_count)

---

### QA-P1-2: Нет теста на идемпотентность build_sup

**Файл:** `scripts/build_sup.py`

**Что не так:** Скрипт `build_sup.py` заявлен как идемпотентный (комментарий в строке 5: "Идемпотентен: повторный запуск даёт"), но теста на проверку идемпотентности нет. При изменении шаблона или логики легко сломать идемпотентность без обнаружения.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
test_content = ''
for f in Path('tests').glob('test_*.py'):
    test_content += f.read_text(encoding='utf-8')
if 'idempotent' not in test_content.lower():
    print('No idempotency test found')
"
```

**Рекомендация:** Добавить тест, который:
1. Запускает build_sup
2. Сохраняет хеши всех файлов
3. Запускает build_sup повторно
4. Сравнивает хеши

---

### QA-P1-3: Нет теста на валидность HTML sup

**Файл:** `docs/sup/*.html` (131 файл)

**Что не так:** Тестов на валидность HTML (закрытые теги, правильная структура) нет. При генерации sup-страниц легко получить невалидный HTML без обнаружения.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
test_content = ''
for f in Path('tests').glob('test_*.py'):
    test_content += f.read_text(encoding='utf-8')
if 'valid' not in test_content.lower() or 'html' not in test_content.lower():
    print('No HTML validity test found')
"
```

**Рекомендация:** Добавить тест, который проверяет:
- Наличие DOCTYPE
- Закрытые теги (html, head, body)
- Наличие title
- Отсутствие дублирующихся id

---

## 4. P2 (nice to have)

### QA-P2-1: test_silent_handlers ключуется по номеру строки

**Файл:** `tests/test_silent_handlers.py:71-126`

**Что не так:** Словарь `ACCEPTED_UNPROTECTED` ключуется `(файл, номер строки)`. Любая правка в файле выше по тексту сдвигает номера строк и роняет тест. Это известный техдолг (ROADMAP #52), но он остаётся хрупким местом.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
content = Path('tests/test_silent_handlers.py').read_text(encoding='utf-8')
if '(\"tracker.js\", 291)' in content:
    print('Line numbers hardcoded in ACCEPTED_UNPROTECTED')
"
```

**Рекомендация:** Заменить ключ на содержимое guard'а или контекст вокруг него.

---

### QA-P2-2: 123 карточки с null forms

**Файл:** `docs/data.json`

**Что не так:** 123 из 130 карточек имеют `"forms": null`. Поле `forms` не используется в шаблоне `sup.html.j2`, поэтому это не критично, но может быть проблемой при добавлении новых полей в шаблон.

**Как воспроизвести:**
```bash
python -c "
import json
with open('docs/data.json', encoding='utf-8') as f:
    data = json.load(f)
cards = data if isinstance(data, list) else data.get('cards', [])
null_forms = [c for c in cards if c.get('forms') is None]
print(f'Null forms: {len(null_forms)}')
"
```

**Рекомендация:** Либо удалить поле `forms` из data.json, либо добавить тест на его обработку в шаблоне.

---

### QA-P2-3: Нет теста на broken links в sup

**Файл:** `docs/sup/*.html`

**Что не так:** Тестов на проверку внутренних ссылок в sup-страницах нет. Сейчас broken links нет (проверено вручную), но при добавлении новых страниц или переименовании slug'ов легко получить битые ссылки.

**Как воспроизвести:**
```bash
python -c "
import re
from pathlib import Path
sup_dir = Path('docs/sup')
broken = []
for html_file in sup_dir.glob('*.html'):
    content = html_file.read_text(encoding='utf-8')
    for m in re.finditer(r'href=[\"\\']([^\"\\']+\\.html)[\"\\']', content):
        href = m.group(1)
        if href.startswith('sup/'):
            target = Path('docs') / href
            if not target.exists():
                broken.append((html_file.name, href))
print(f'Broken links: {len(broken)}')
"
```

**Рекомендация:** Добавить тест, который проверяет все внутренние ссылки в sup-страницах.

---

## 5. Что чинить в v5.6.1

1. **QA-P1-1:** Добавить тесты для критичных скриптов (build_api, build_key_sources, build_interactions, check_state, validate_proposal)
2. **QA-P1-2:** Добавить тест на идемпотентность build_sup
3. **QA-P1-3:** Добавить тест на валидность HTML sup
4. **QA-P2-1:** Заменить ключ в ACCEPTED_UNPROTECTED на содержимое guard'а (техдолг #52)
5. **QA-P2-2:** Удалить поле `forms` из data.json или добавить тест на его обработку
6. **QA-P2-3:** Добавить тест на broken links в sup

---

## 6. Проверенные известные техдолги

| Техдолг | Статус | Примечание |
|---------|--------|------------|
| ROADMAP #52: test_silent_handlers ключуется по номеру строки | Подтверждён | ACCEPTED_UNPROTECTED использует (файл, номер строки) |
| ROADMAP #85: Playwright route.abort() не срабатывает | Не проверялся | Требует браузерного теста |
| ROADMAP #87: check_state.py показывает tests:989, pytest собирает 792 | Подтверждён | 989 собрано, 790 passed + 2 skipped = 792 |

---

## 7. Edge cases в data.json

| Edge case | Количество | Статус |
|-----------|------------|--------|
| Карточка с 0 эффектами | 0 | OK |
| Карточка с 0 источниками | 0 | OK |
| Поле null в forms | 123 | Не критично (не используется в шаблоне) |
| Поле null в interactions | 0 | OK |
| Дубли id | 0 | OK |

---

## 8. Покрытие модулей src/

| Модуль | Тесты | Статус |
|--------|-------|--------|
| src/content.py | test_content_module.py, test_content_latin.py | COVERED |
| src/config.py | test_src_config.py | COVERED |
| src/ct_terms.py | test_src_ct_terms.py | COVERED |
| src/wiki_map.py | test_src_wiki_map.py | COVERED |

---

## 9. Заключение

- **P0:** 0
- **P1:** 3 (критичные скрипты без тестов, нет теста на идемпотентность build_sup, нет теста на валидность HTML sup)
- **P2:** 3 (test_silent_handlers ключуется по номеру строки, 123 карточки с null forms, нет теста на broken links в sup)

**Общий статус:** Тесты проходят (790 passed, 2 skipped), критичных проблем нет. Основные риски — отсутствие тестов на критичные скрипты и генератор sup.
