# FIX-77 — Перевод данных карточек на английский

Дата: 26.10.2026. Ветка: `v5.6.5-dev`. База: `a5e02f52`.

## Проблема

На английской версии карточек (`docs/sup/*.html`) переводился только интерфейс:
about, механизмы, дозировки, мифы, осторожность и взаимодействия оставались
на русском. Плюс смешанные строки вида «Look for the “триглицерид” form» —
EN-шаблон `sup.lookForForm` подставлял русскую форму из `data.json`.

Причина: `docs/data.json` — единственный источник контента, и он на русском.
130 sup-страниц статически пре-рендерятся из него через `scripts/build_sup.py`.

## Решение: оверлей `docs/data_en.json`

Перевод не хранится внутри `data.json` (не раздуваем основной файл и не ломаем
русскую версию). Вместо этого — отдельный файл-оверлей:

```json
{
  "_meta": {"source": "docs/data.json", "translator": "google-translate-free", "cards": 130},
  "supplements": {
    "Омега-3": {"name": "Omega-3", "about": "...", "mechs": [...], ...}
  }
}
```

Ключ — русский `id` карточки (он же `name`/`title` в `data.json`).
В оверлее лежат **только переведённые поля**; отсутствующее поле → русский
фолбэк. Мердж делается по `id` поверх базовых данных:

- `docs/script.js` — `ensureFullData()` → `Promise.all([fetchJson('data.json'), loadEnCards()])`
  + `mergeEnCard()`; каталог на `index.html` мержит оверлей до `initApp()`;
  `openModal()` и `renderCompare()` переведены на `ensureFullData()`.
- `docs/hactar.js` — `loadData()`, `loadFullMechs()`, `loadFullData()`.
- `docs/i18n.js` — `loadEnCards()` (только при `LOCALE === 'en'`, один fetch,
  кеш промиса), `mergeEnCard()`, `applyEnSupData()`, `applyEnCatalog()`.
- Sup-страницы статические, поэтому в шаблон `templates/sup.html.j2` добавлены
  маркеры `data-sup="<поле>"` / `data-sup-i="<индекс>"`, а `i18n.js` на
  `DOMContentLoaded` подставляет переведённые значения, title/meta/og/twitter
  и пересобирает `.shop-look`.

База пути: `EN_DATA_BASE = /\/sup\//.test(location.pathname) ? '../' : ''` —
без этого `data_en.json` давал 404 на вложенных страницах.

## Скрипт `scripts/translate_data.py`

- Google free endpoint (`translate.googleapis.com/translate_a/single`), POST,
  маркеры `⟦N⟧` — несколько строк уходят одним запросом, ответ режется по
  маркерам; при несовпадении количества — поштучный фолбэк.
- Кеш `logs/translate_cache_ru_en.json` (gitignored, 2418 записей) — повторный
  прогон бесплатный и возобновляемый.
- Курируемые словари (не через MT): `NAME_EN` (130 имён), `VERDICT_EN` (3),
  `STRENGTH_EN` (5), `CATEGORY_EN` (54 базовых термина), `FORM_OVERRIDES`
  (рваные формы вида `экстракт (SHR-5`, `МК-7`, соли), `SYNERGIST_EN`.
- Пред-подстановка аббревиатур перед MT (ССЗ→CVD, ЖКТ→GI, РКИ→RCT, НПВС→NSAIDs,
  ФП→AF, ТГ→TG …) + постобработка единиц (мкг/мг/г/мл/МЕ → mcg/mg/g/ml/IU).
- Не переводятся: `pubmed_term`, `key_sources`, `ma_top3` (уже английские),
  `interactions.severity` (low/medium/high/critical).
- CLI: `python scripts/translate_data.py` (полный), `--check` (валидация:
  130 карточек, 0 кириллицы, совпадение длин списков), `--limit N`.

Результат: `docs/data_en.json` — 312 209 Б, 130 карточек, 0 кириллицы.

## Смешанные строки

- `sup.lookForForm` больше не получает русскую форму: `.shop-look` целиком
  перезаписывается из оверлея (`Look for the “triglyceride” form on the label…`).
- 20 строк EN-словаря вида `Find Магний on Ozon` переписаны на английские имена
  (Magnesium, Omega-3, Vitamin D, Vitamin B12, Zinc, Curcumin, Iron, Melatonin,
  Vitamin C, Creatine).
- Добавлены ключи `index.pop.<slug>.name` (10 плиток «Популярные добавки») —
  раньше имена плиток были захардкожены по-русски.
- Новый файл `docs/effect_labels_en.json` (18 подписей эффектов для чипов) —
  `effect_labels.json` остаётся русским.

Контроль: `keys=1197 cyrillic_values=0` в EN-словаре;
`tests/test_i18n_no_russian.py` — 17 passed.

## Проверка в браузере (Playwright, SW снят + `caches.delete`)

| Страница (lang=en) | Результат |
|---|---|
| `sup/omega-3.html` | h2 «Omega-3», about/mechs/dosage/myths/caution/interactions на английском, `cyrCount: 0` |
| `sup/index.html` | 130 карточек, имена/категории/вердикты/фильтры английские, `cyrCount: 0` |
| `index.html` | каталог и плитки на английском, чипы эффектов «Sleep», «Stress / anxiety», `cyrCount: 0` |
| `hactar.html?tab=overview` | эффекты/дозы/грейды английские; 4 кириллических слова — «Яндекс Маркет» (название магазина, оставлено осознанно) |

## Тесты

```
python -m pytest -q -m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"
→ 1802 passed, 215 deselected, 0 failed (76.91s)
```

Снапшоты не перегенерировались: вёрстка не менялась — добавлены только
инлайновые `<span>`-обёртки с `data-sup*`, CSS-правил для `h1 span` нет.

## Бампы версий

| Что | Было → стало |
|---|---|
| `i18n.js?v=` | 13 → 15 (151 файл: 149 страниц + 2 шаблона) |
| `script.min.js?v=` | 299 → 301 (`index.html`) |
| `hactar.js?v=` | 31 → 33 (`hactar.html`) |
| `sw.js CACHE_VERSION` | v160 → v161 (+ комментарий-бамп) |
| `sw.js DATA_RE` | `/\/data(_index)?\.json$/` → `/\/data(_index|_en)?\.json$/` |

`sw.js`: `data_en.json` попадает в network-first ветку, `effect_labels_en.json`
добавлен в `STATIC_ASSETS`. `style.min.css?v=462` не менялся.

## Ограничения (осознанно вне объёма)

- **Граф** (`docs/graph_data.json`, ~360 КБ) — подписи узлов остались русскими;
  при EN-режиме `hactar.js` берёт `effect_labels_en.json` для подписей метрик,
  но имена узлов графа не переводятся.
- **Названия маркетплейсов** («Яндекс Маркет») не переводятся — это имена
  сервисов, а не контент.
- Перевод машинный (Google), без редакторской вычитки 130 карточек; при
  необходимости правится точечно в `docs/data_en.json` — скрипт перезаписывает
  файл целиком, поэтому правки нужно либо вносить после прогона, либо
  добавлять в курируемые словари скрипта.
