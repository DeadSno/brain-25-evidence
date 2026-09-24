# Архитектура brain-25-evidence

Как устроен проект: от PubMed до HTML-страницы. Всё воспроизводимо одной командой.

---

## Общая схема

```
        ┌────────────────────────────────────────────────────┐
        │  Внешние источники (открытые API)                  │
        │  • PubMed E-utilities (esearch/esummary/efetch)    │
        │  • OpenAlex (цитирования)                          │
        │  • Wikipedia REST (просмотры)                      │
        │  • ClinicalTrials.gov API v2 (испытания)           │
        └────────────────────┬───────────────────────────────┘
                             │
                    scripts/fetch_*.py
                    scripts/recalc_*.py
                             │
                             ▼
        ┌────────────────────────────────────────────────────┐
        │  docs/data.json — единый источник для фронта      │
        │  103 карточки, 595 KB                              │
        │  Поля: verdict, grade, mechs, effects, dosage,    │
        │         key_sources, hedges_g, interactions,       │
        │         about, who_needs, onset, myths, ...        │
        └────────────────────┬───────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────────────┐
        │  Frontend (static HTML + vanilla JS)              │
        │  • index.html       — дашборд, радар, сравнение  │
        │  • map.html         — карта механизмов           │
        │  • interactions.html — карта связей (vis-network)│
        │  • atlas.html       — атлас 25×103                │
        │  • calculator.html  — калькулятор БАДов          │
        └────────────────────┬───────────────────────────────┘
                             │
                             ▼
                  GitHub Pages (deadsno.github.io)
```

---

## Слои данных

### 1. Сырьё (`data/raw/`)

- `pubmed_evidence.csv` — результат массового esearch по 103 запросам
- `prices_wb_history.csv` — архив (не используется)

### 2. Обработка (`data/processed/`)

- `archive/pubmed_v12.csv` — метрики PubMed по каждой карточке (архив)
- `xml_meta.json` — parsed XML из Europe PMC (funding/COI)
- `funders_top.csv`, `countries_top.csv` — топ фандеров и стран

### 3. Публичный фронт (`docs/`)

- **`data.json`** — 103 карточки, ~595 KB. Единый источник для всех страниц
- `data_pubmed_terms.json` — поисковые запросы для PubMed (120 записей)
- `dosage_parsed.json` — распарсенные дозы (min/max/unit/freq, weight_based)
- `interactions_graph.json` — граф связей между добавками и лекарствами
- `pairs.json` — рекомендуемые пары добавок (для калькулятора)
- `profiles.json` — 8 профилей-пресетов
- `hedges_g_all.json` — все кандидаты g (отладка)

---

## Пайплайн данных

### Полное обновление одной командой

```bash
python scripts/update_all.py --apply
```

4 шага, ~30 минут:

| Шаг | Скрипт | Что делает |
|-----|--------|------------|
| 1 | `fetch_metrics.py --all --apply` | wiki / citations / ongoing для 103 |
| 2 | `recalc_science_index.py --apply` | scienceIndex = RCT + 5×MA |
| 3 | `fetch_hedges_g.py --apply` | Hedges' g из топ-MA (2 прохода) |
| 4 | `enrich_dois.py --apply` | DOI в key_sources |

**Конвенция:** `--apply` = запись, без флага = dry-run. У `fetch_metrics.py` свой `--dry-run`.

### Ключевые технические решения

**ScienceIndex** = `RCT + 5 × MA` — количество, не сила эффекта. Verdict ставится вручную по топ-2 MA.

**Hedges' g — двухпроходный алгоритм** (`fetch_hedges_g.py`):
1. Проход 1: собрать всех кандидатов для каждой карточки
2. Проход 2: сортировка по числу кандидатов + `used_pmids` — **один PMID = одна карточка**

Это устраняет cross-matching: раньше один PMID попадал в 5 карточек с одинаковым g.

**Валидация данных:**
- `audit_stale.py` — PMIDs старше 5 лет (квартальный прогон)
- `validate_sources.py` — проверка key_sources на наличие DOI/PMID
- `e2e_smoke.py` — smoke-тесты сайта (headless)

---

## Frontend

### Принципы

- **Vanilla JS.** Никаких фреймворков — сайт статический на GitHub Pages
- **Один `data.json`** — источник данных, разные страницы рендерят разное
- **Inline JS** в четырёх HTML (карты и калькулятор) — компромисс: плюс автономность, минус размер файлов
- **PWA v31** — service worker кэширует `data.json` и статику; офлайн-режим работает

### Страницы

| Файл | Строк | Что |
|------|-------|-----|
| `script.js` | 926 | Main-логика index.html: карточки, модалка, графики, фильтры |
| `calculator.html` | 777 | Калькулятор: дозы, конфликты, профили, рекомендации |
| `interactions.html` | 764 | Vis-network граф связей |
| `atlas.html` | 729 | Vis-network атлас 25 тегов × 103 добавки |
| `map.html` | 598 | Цепочки механизмов + оверлей |
| `style.css` | 530 | Общие стили |
| `index.html` | 362 | Дашборд |

### Библиотеки (CDN, без сборки)

- **Chart.js 4.4.1** — графики (bubble, quadrant, radar, line)
- **vis-network 9.1.9** — графы (карты связей и атлас)

---

## Калькулятор БАДов

### Данные

- **`dosage_parsed.json`** — 81 доза (для 22 новых — fallback), распарсено регуляркой + ручные
- **`interactions`** в `data.json` — 103 карточки, 169 пар всего
- **`pairs.json`** — 16 пар для рекомендаций
- **`profiles.json`** — 8 профилей

### Логика

1. **Пользователь** вводит вес/пол/возраст/состояние
2. **Добавляет** БАДы через поиск или профиль
3. **Расчёт:**
   - Проверка дозы: `min × 0.9 … max × 1.1` (для weight_based — диапазон пересчитывается по весу)
   - UL-проверка: явный UL в `upper_limit` (не «безопасно до X»)
   - Конфликты: разбивка на 🌿 добавки / 💊 лекарства / 🍷 вещества
   - Синергии: пересечение с `pairs.json`
   - Предупреждения: мужчина+железо, 60+, беременность/лактация

4. **Sharing:** URL `?list=Креатин:5,Омега-3:2` + localStorage

---

## Тесты

**112 тестов, все зелёные.**

| Файл | Что покрывает |
|------|---------------|
| `test_schema.py` | JSON-схема `data.json` |
| `test_site_data.py` | данные сайта соответствуют карточкам |
| `test_snapshot.py` | data.json не изменился без `UPDATE_SNAPSHOT=1` |
| `test_education.py` | low-блоки, interactions привязаны |
| `test_validate_sources.py` | key_sources |
| `test_js_syntax.py` | `node --check` для `script.js` |
| `test_v27_manifest.py` | PWA manifest |
| `test_migrate_key_sources.py` | миграция |
| `test_search_sources.py` | поиск источников |

**Snapshot-тесты — защита от случайных правок.** Если `data.json` изменился без `UPDATE_SNAPSHOT=1`, тест падает.

### CI

`.github/workflows/tests.yml` — pytest + `node --check` на каждый push в main.

`.github/workflows/watchdog.yml` — раз в неделю (cron) проверяет links + schema.

---

## Воспроизводимость

### Клонирование и запуск

```bash
git clone https://github.com/DeadSno/brain-25-evidence.git
cd brain-25-evidence
pip install -r requirements.txt

python -m pytest tests/ -q           # 112 passed
python docs/serve.py                 # → http://localhost:8000/
```

### Верификация данных

```bash
python scripts/audit_stale.py        # PMIDs старше 5 лет
python scripts/validate_sources.py   # key_sources
python scripts/e2e_smoke.py          # сайт работает
```

---

## Манифест проекта

**Правдивость данных важнее охвата и красоты.**

Что это значит на практике:

1. **Verdict вручную** по топ-2 MA — не автоматика
2. **Hedges' g** = сила эффекта, отдельно от scienceIndex (количества)
3. **Никаких выдумок в adv-полях.** Только из abstracts, проверяется аудитом
4. **Честные признания:** если свежих MA нет — так и пишем, не заменяем старыми
5. **Прозрачная методология:** `methodology.html`, все скрипты открыты
6. **Никаких медицинских советов:** дисклеймер на каждой странице

См. подробнее: [methodology.html](https://deadsno.github.io/brain-25-evidence/methodology.html)

---

## Что дальше

См. [ROADMAP.md](ROADMAP.md). Открытые направления:

- Расширение базы (100+ добавок)
- PDF-экспорт карточек для врачей
- Отдельные страницы под каждую добавку (SSG)
- Публичный API (`docs/api/v1/supplements.json`)

---

## Лицензия

MIT. Используйте данные как угодно, указывайте источник.