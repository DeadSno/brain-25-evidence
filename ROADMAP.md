# ROADMAP — brain-25-evidence

**Обновлено:** 2026-09-22
**Состояние:** 81 БАД, v3.2.0, 113 тестов зелёные.
**Цель:** v2.0 — Data Platform с 150+ добавками, DWH, BI, публичным API.
**Срок:** 2.5-3 месяца в темпе 20+ часов/неделю.

---

## 📊 Текущее состояние (v3.2.0)

| Компонент | Статус |
|---|---|
| База | 81 карточка |
| Hedges' g | 63/81 (59 с CI) |
| Mech | 81/81, среднее 3.07 |
| Adv-поля (Q1.4) | 81/81 ✅ |
| DOI в key_sources | 236/238 (98.7%) |
| Калькулятор | ✅ профили, рекомендации, weight_based |
| PWA | ✅ v33, офлайн-режим |
| Mobile | ✅ адаптив 5 страниц |
| SEO | ✅ sitemap, og-мета, robots |
| XSS | ✅ esc() везде |
| Производительность | ✅ data_index.json (48 KB, ×10) |
| CI | ✅ pytest + node --check + sync_version |

**Источники:** PubMed, OpenAlex, Wikipedia, ClinicalTrials.gov.

---

## ✅ Сделано (история)

### v3.0
- Аудит 81/81 добавок по PRISMA, грейды A=8/B=35/C=26/D=12
- 14 коммитов, 2 тега релиза

### v3.1
- Чистка `docs/`, палитра грейдов, methodology переписан
- WB-цены удалены, заголовок сменён

### v3.2.0
- Калькулятор БАДов (777 строк)
- Аудиты q14 D1/D2 — 5 + 10 PMIDs
- SEO: sitemap, og-мета, robots
- Документация: ARCHITECTURE / CONTRIBUTING / DATA_SOURCES
- Ops: `update_all.py`, `audit_stale.py`, `build_index.py`
- XSS-fix (37 мест + хелперы)
- Производительность: `data_index.json` + prefetch (×10)
- CI: `sync_version.yml`
- Mobile: grid-шапка, модалка, qaGrid, адаптивные пузыри
- Статья на Хабре + Пикабу

---

## 🎯 План до v2.0 — что делаем точно

**Принцип:** лучше сделать 80% хорошо, чем 100% плохо. Все оценки с буфером 30%.

### Фаза A — Tooling + Data (2 недели)

#### A1. `scripts/add_supplement.py` (1 день) ✅
Полуавтомат добавления:
- PubMed esearch → топ-20 MA, scienceIndex, metaCount, RCT
- Hedges' g через существующий pipeline
- citations (OpenAlex), wiki (Wikimedia), ongoing (ClinicalTrials)
- Заготовка карточки с adv-полями `_пусто_`

**Эффект:** 20 → 5 мин на карточку.

#### A2. Time series (2-3 дня) ✅
- `time_series_pubmed` — 81 × 10 лет = **810 строк**
- `time_series_wiki` — 81 × 24 мес = **1944**
- `time_series_citations` — 81 × 10 = **810**

**Итого:** +3600 строк. Тренды, сезонность, forecasting.

#### A3. Papers entity (1 день) ✅
- Таблица `papers` — все PMIDs, не только топ-3
- Связка `paper_supplement` many-to-many
- Fields: title, authors, journal, year, type, citations, DOI

**Итого:** +3000 строк.

#### A4. Interactions matrix (2-3 дня) ⚠️ **урезано**
- **Реально:** 300-500 пар (не 1000), из карточек + Wikipedia
- **Не тянем:** DrugBank (лицензия), Drugs.com (парсинг ToS)
- Если API/источник не найдётся — делаем **только из карточек** (~300)

---

### Фаза B — Расширение до 150 (2-3 недели)

**По 8-10 добавок в день через `add_supplement.py`.**

**Что добавляем (60-70 добавок):**
- Витамины: A, K2, B1, B2, B3, B5, B6, холин, инозитол (+9)
- Минералы: медь, марганец, калий, бор, кремний (+5)
- Аминокислоты: лизин, метионин, орнитин, HMB, карнозин (+5)
- Травы: женьшень, астрагал, босвеллия, шлемник, пассифлора, лаванда (+8)
- Грибы: чага, шиитаке, майтаке (+3)
- Пробиотики: S. boulardii, LGG, B. lactis (+3)
- Жирные кислоты: EPA, DHA, GLA (+3)
- Антиоксиданты: глутатион, PQQ, кверцетин, сульфорафан (+4)
- Специализированные: берберин, MSM, бетаин, гимнема (+4)

**Итого: +44 минимум, +70 при удаче → 125-150 добавок.**

**Вехи:** 100 → 120 → 150.

**Fallback:** если выгорание на 100-й — останавливаемся на 120, это уже норм.

---

### Фаза C — Data Platform (1-1.5 недели)

#### C1. DuckDB + dbt (4 дня) ✅
- `pip install duckdb dbt-core dbt-duckdb`
- Структура DWH:
  - `stg_supplements.sql`, `stg_papers.sql`, `stg_timeseries.sql`
  - `dim_categories.sql`, `dim_papers.sql`
  - `fct_supplement_metrics.sql`, `fct_interactions.sql`
  - `agg_top_by_grade.sql`, `agg_category_stats.sql`
- **30-50 SQL-запросов** (не 50+)

#### C2. Тесты качества (1 день) ✅
- `dbt test` — unique, not_null, accepted_values

---

### Фаза D — Analytics + BI (3-4 дня)

#### D1. Events tracking (1 день) ✅
- **Umami** на Vercel Free
- 10 событий (не 15): `card_open`, `search`, `calculator_use`, `verdict_click`, `share`

#### D2. BI Dashboard (2-3 дня) ⚠️ **риск с Docker**
- **Metabase** через Docker
- **Fallback:** Metabase Cloud free tier для open-source проектов
- **Fallback 2:** Evidence.dev (markdown + SQL, статичный)

---

### Фаза E — Public API + Telegram (2 дня)

#### E1. Public API (1 день) ✅
- `docs/api/v1/supplements.json`
- `docs/api/v1/schema.json`
- Примеры curl

#### E2. Telegram-бот (1 день) ✅
- `@brain25_bot` — поиск, `/random`, `/top`
- Fly.io (бесплатно)

---

## 🎁 Что постараемся сделать (v2.1+)

**Идёт после релиза v2.0, если будет ресурс и мотивация.**

### A/B-тесты (4-5 дней) ⚠️ **зависит от трафика**
- 2-3 гипотезы
- t-test, confidence intervals
- **Требует 500+ юзеров/неделя.** Если меньше — откладываем

### ML grade prediction (5-7 дней) ⚠️ **слабо статистически**
- **Проблема:** 150 карточек × 15 features — модель переобучится
- Accuracy будет **65-75%**, не 90%
- **Fallback:** для портфолио ML используем **Lending Club** (100K строк)

### FAERS — побочные эффекты (3-4 дня) ✅
- Open FDA API → 5000+ строк
- Цепляющая тема для Хабра

### Outcomes / Populations (2-3 недели) ⚠️ **урезано**
- **Только на 30-50 топовых добавках** (не на всех)
- 30 × 4 = 120 строк outcomes
- 30 × 3 = 90 строк populations

### Regulatory status (2-3 дня) ✅
- РФ / EU (EFSA) / US (FDA) — 150 × 3 = 450 строк

### Meta-analysis table (1 неделя) ✅
- Все MA как отдельная сущность
- N studies, N participants, effect, CI, I²

### Brands / производители (1 неделя) ⚠️ **риск парсинга**
- ГРЛС без API — только web
- **Fallback:** если не парсится — пропускаем

---

## 📋 Долгий хвост (не блокеры)

Из старого бэклога, разберём в паузах:
- Inline JS → модули
- !important чистка
- Семантический аудит 51 карточки
- 10 evidence-файлов батчей 1-2
- Hedges' g для 18 карточек
- Разбивка data.json (полная)

---

## 📈 Что даёт v2.0

| Сейчас (v3.2.0) | v2.0 |
|---|---|
| 81 карточка | **125-150 карточек** |
| ~2500 значений | **~10 000 строк** |
| 1 таблица | **6-8 таблиц** |
| Google-скрипт | **DWH на DuckDB + dbt** |
| Статика | **BI-дашборд** |
| Нет API | **Public API + Telegram** |

**Позиционирование в резюме:**
> Data Analyst / Junior Data Engineer: ETL из 4+ внешних API, DWH на DuckDB, dbt-модели, BI в Metabase, публичный API.

---

## 🎯 Приоритеты

1. **Фаза A** — Tooling + Data (2 нед)
2. **Фаза B** — Расширение до 150 (2-3 нед, параллельно)
3. **Фаза C** — DWH на DuckDB (1 нед)
4. **Фаза D** — Analytics + BI (4 дня)
5. **Фаза E** — API + Telegram (2 дня)

**Итого до v2.0: 6-8 недель** (не 12-14 как в первой версии).

**Дальше — v2.1+ по остаточному принципу.**

---

## ⚠️ Риски и fallback

| Риск | Fallback |
|---|---|
| Выгорание на 100-й карточке | Остановиться на 120 |
| Docker не работает | Metabase Cloud или Evidence.dev |
| A4 interactions не находится | Только из карточек (~300) |
| A/B нет трафика | Пропустить, вернуться позже |
| ML слабый | Заменить на Lending Club (100K) |
| ГРЛС не парсится | Пропустить, компенсировать Regulatory |

---

**Манифест:** правдивость данных важнее охвата и красоты. Прозрачная методология, никаких медицинских рекомендаций, MIT.