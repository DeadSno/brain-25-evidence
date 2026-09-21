# Как внести вклад

Спасибо что зашли. Этот документ — для тех, кто хочет **исправить ошибку, добавить добавку или улучшить код**.

**Манифест:** правдивость данных важнее охвата и красоты. См. [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Быстрая карта

| Что | Куда |
|-----|------|
| Нашли ошибку в данных | → [issue `data-error`](.github/ISSUE_TEMPLATE/data-error.md) |
| Хотите добавить добавку | → [issue `new-supplement`](https://github.com/DeadSno/brain-25-evidence/issues/new) |
| Есть PR с фиксом | → [fork → PR](#pull-request) |
| Хотите запустить локально | → [ARCHITECTURE.md](ARCHITECTURE.md#воспроизводимость) |

---

## Три типа вклада

### 1. Сообщить об ошибке в данных

**Не создавайте PR, если не уверены в фиксе.** Сначала — issue.

Что указать в issue:
- **Карточка:** ID добавки (например «Креатин»)
- **Поле:** `verdict`, `grade`, `dosage`, `about` и т.д.
- **Что не так:** «в myths написано X, но в PMID 12345678 сказано Y»
- **Источник:** PubMed PMID / DOI / ссылка

Если вы уверены и хотите сразу PR — см. ниже.

### 2. Добавить добавку

**Процесс длинный** — это контент, не код. Нужно:

1. **Собрать evidence:**
   - Найти 2+ мета-анализа в PubMed
   - Записать PMIDs в `key_sources`
2. **Заполнить 12 полей карточки** в `docs/data.json`:
   - Базовые: `verdict`, `grade`, `effects`, `dosage`, `course`, `caution`
   - Расширенные: `about`, `who_needs`, `onset`, `myths`, `food_sources`, `guidelines`, `how_to_choose`
3. **Добавить PubMed-запрос** в `docs/data_pubmed_terms.json`
4. **Пересчитать метрики:**
   ```bash
   python scripts/recalc_science_index.py --apply
   python scripts/fetch_metrics.py --all --apply
   python scripts/fetch_hedges_g.py --apply
   ```
5. **Snapshot + тесты:**
   ```bash
   $env:UPDATE_SNAPSHOT="1"; pytest tests/test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT
   pytest -q
   ```

**Перед началом — создайте issue с описанием.** Мы обсудим, стоит ли включать в базу.

### 3. Улучшить код / UI

Просто PR. Но убедитесь что:

- `pytest -q` → все зелёные
- `node --check docs/script.js` → молчит
- Если меняете `data.json` — обновили snapshot

---

## Правила данных

### Обязательно

1. **Никаких выдумок.** Каждый факт — из abstracts. Если данных нет — так и пишем: «свежих МА нет»
2. **Verdict вручную.** Не автоматика — по топ-2 мета-анализам
3. **Стиль короткий.** См. карточку «Креатин» как эталон
4. **Длины полей:**
   - `about`: 51-101 символов
   - `who_needs`: 57-127
   - `onset`: 40-89
   - `myths`: 85-145
   - `food_sources`: 35-106
   - `guidelines`: 58-121
   - `how_to_choose`: 49-109
5. **PMIDs в `key_sources` должны существовать.** Проверка:
   ```bash
   python scripts/validate_sources.py
   ```

### Нельзя

- ❌ Медицинские советы («принимайте при…», «лечит…»)
- ❌ Маркетинг («мощный», «уникальный», «революционный»)
- ❌ Прямые сравнения с лекарствами без оговорок
- ❌ Ссылки на коммерческие источники (бренды, магазины)
- ❌ Изменять `docs/data.json` вручную без теста snapshot

---

## Стиль кода

### Python

- Python 3.12+
- f-strings
- `pathlib` вместо `os.path`
- Type hints (`def foo(x: int) -> str:`)
- Docstring в начале файла

### JavaScript

- Vanilla JS, без сборки
- `let`/`const`, не `var`
- Template literals (`` ` ``)
- Комментарии секций: `// ── Секция ──`

### HTML/CSS

- Semantic HTML (`<header>`, `<nav>`, `<aside>`)
- CSS-переменные для темы (`--apanel`, `--aborder`)
- Адаптив через `@media (max-width: 640px)`

---

## Pull Request

### Перед PR

```bash
# 1. Все тесты
pytest -q

# 2. JS-синтаксис
node --check docs/script.js

# 3. Snapshot (если меняли data.json)
$env:UPDATE_SNAPSHOT="1"; pytest tests/test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT
```

### Что включить в PR

- **Один PR = одна задача.** Не смешивайте «фикс данных» и «рефакторинг CSS»
- **Описание:** что меняете, зачем, ссылки на PMIDs
- **Скриншот** если визуальные изменения
- **Без `--no-verify`.** Pre-push hook прогоняет тесты — это защита

### Коммиты

Атомарные. Формат:

```
тип(область): краткое описание

- Деталь 1
- Деталь 2
```

Типы: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.

Примеры:
```
feat(mechs): батч 7 — Витамин K2, Хром, Инозитол, Рибофлавин, Биотин
fix(q14): аудит группа D — формулировки + дубли
docs(readme): актуализация под v3.1
```

---

## Процесс ревью

1. **Автоматика:** CI прогоняет тесты на GitHub Actions
2. **Ручное ревью:** я смотрю каждую правку в `data.json` — манифест требует точности
3. **Мердж:** обычно squash-merge — история чистая

**Долгие PR** (новые добавки, крупный рефакторинг) — обсуждаем в issue перед стартом. Не хочу чтобы вы делали работу, которую не приму.

---

## Что не примем

- Добавки без доказательной базы (только «маркетинг»)
- Изменения в adv-полях без PMIDs
- Косметические PR без обсуждения (названия файлов, форматирование)
- Замены существующих PMIDs без обоснования
- PR с `--no-verify`

---

## Вопросы

- **Про данные:** [issue](https://github.com/DeadSno/brain-25-evidence/issues/new)
- **Про архитектуру:** см. [ARCHITECTURE.md](ARCHITECTURE.md)
- **Про методологию:** [methodology.html](https://deadsno.github.io/brain-25-evidence/methodology.html)

---

## Лицензия

MIT. Отправляя PR, вы соглашаетесь с лицензией.