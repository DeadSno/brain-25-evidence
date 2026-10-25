# A-1.1 — хотфикс главной после A-1

Дата: 22.10.2026. Ветка `v5.6.5-dev`. Основание: `a9fbb3f5` (A-1).

## Что сделано

### 1. Дублирующая кнопка Hactar убрана из hero

`docs/index.html`, блок `.hero-cta`: кнопка `<a class="btn calc" href="hactar.html">🧠 Открыть Project Hactar →</a>`
удалена. Ниже по той же странице осталась большая карточка Project Hactar
(`.card-featured-lg`, «Открыть Project Hactar →») — главный путь на Hactar теперь один.

### 2. «Найти свою добавку» понижена до tertiary

Было: `<a class="btn" href="#cardsContainer">` — вторичная кнопка с заливкой и рамкой.
Стало: `<a class="hero-search" href="#cardsContainer">🔍 Найти свою добавку →</a>` — текстовая
ссылка, без заливки и без рамки.

Правило живёт в локальном `<style>` главной (общий `style.css` не трогаем: правка тянет
бамп `?v=` в 145 страницах):

```css
.hero-cta .hero-search {
  display: inline-flex; align-items: center; gap: .45rem;
  min-height: 44px; padding: .3rem .15rem;
  color: var(--muted); font-size: .95rem; font-weight: 500;
  text-decoration: underline; text-underline-offset: .18em;
  border-radius: 8px; transition: color .15s;
}
@media (hover:hover) { .hero-cta .hero-search:hover { color: var(--accent); } }
```

Селектор `.hero-cta .hero-search` — специфичность (0,2,0) — перебивает общий
`html:not(.light) a` (0,1,1), иначе ссылка осталась бы акцентной (`--accent-2`).

Замер в браузере (Playwright, 1280×900):

| Свойство | Значение |
|---|---|
| фон | `rgba(0, 0, 0, 0)` (заливки нет) |
| рамка | `0px` (рамки нет) |
| цвет | `rgb(154,154,160)` = `--muted` (тёмная), `rgb(110,110,115)` = `--muted` (светлая) |
| min-height | `44px` (тап-таргет сохранён) |
| font-size | `15.2px` / `14.4px` на ≤640px |
| подчёркивание | есть (в тёмной теме — от общего правила `a`, в светлой — от нового) |

Контраст: `--muted` 7.2:1 (тёмная) и 4.9:1 (светлая) — AA для обычного текста.

### 3. map.html → редирект на hactar.html?tab=graph

`docs/map.html`, в `<head>` после `og:url`:

```html
<meta http-equiv="refresh" content="0;url=hactar.html?tab=graph">
<link rel="canonical" href="hactar.html">
```

Тело страницы оставлено — так же, как сделано для `interactions.html`,
`calculator.html`, `compare.html` (редирект делает meta refresh, контент остаётся
фолбэком без JS). Canonical указывает на конечный адрес.

Проверка в браузере: `http://localhost:8000/map.html` → адрес вкладки становится
`http://localhost:8000/hactar.html?tab=graph`, активна вкладка «Связи»
(`tabs[mode=links].active = true`, панель `links` не скрыта).

### 4. Побочные правки, без которых правка не рабочая

- `docs/script.js`: селектор обработчика `a.btn[href="#cardsContainer"]` → `a[href="#cardsContainer"]`.
  Ссылка перестала быть кнопкой — уточнение `.btn` больше бы не сработало, и smooth-scroll
  с постановкой фокуса на фильтр молча пропал бы.
  Проверено в браузере: клик → `scrollY 0 → 3204`, `#cardsContainer` у верха экрана,
  фокус на кнопке фильтра «Все эффекты» (`.tagPreset`) — поведение как до правки.
- `docs/index.html`: `script.js?v=291` → `?v=292` (единственная страница, подключающая script.js).
- `docs/sw.js`: `CACHE_VERSION` v114 → v115 + комментарий формата
  `/* Бамп v114 -> v115: <причина> */` (index.html, script.js и map.html входят в
  STATIC_ASSETS без `?v` — сброс кэша держится на CACHE_VERSION).
- `tests/snapshots/{chromium,webkit}/{index,map}-{412,1280}.png` — эталоны пересняты.
- `scripts/e2e_smoke.py`, `scripts/ui_verify.py`: проверки карты переписаны под редирект.
  Прежние проверки ждали `#chain` (цепочка «вещество → мишень → эффект» на map.html) —
  элемента на странице больше нет. Теперь сценарий проверяет сам редирект:
  `map.html?supplement=Эхинацея` → `hactar.html?tab=graph`, вкладка «Связи» активна
  (`#hactarTabLinks[aria-selected="true"]`, панель `#hactarPanelLinks.active`).
  Проверки футера (`faq.html` / `glossary.html`, отсутствие ссылки на несуществующую
  `for_doctors.html`) и trustbar переведены на конечную страницу `hactar.html`.
  Образец поведения уже был в репозитории — так же проверяется редирект
  `compare.html` → `hactar.html`.

## Проверки

| Проверка | Результат |
|---|---|
| hero: единственная ссылка `.hero-cta` | `🔍 Найти свою добавку →` (класс `hero-search`) |
| большая карточка Hactar ниже | есть, `.card-featured-lg`, CTA «Открыть Project Hactar →» |
| map.html → редирект | адрес стал `hactar.html?tab=graph`, вкладка «Связи» активна |
| высота index@412 | 42 744 px (было 42 823) — −0.2 %, гейт `KNOWN_UNCOVERED` (допуск 2 %) в норме |
| `pytest -q` | 1965 passed, 24 skipped, 0 failed (10:13) — см. раздел «Прогон» |

Скриншоты: `reports/A11_index_hero_1280.png`, `reports/A11_index_hero_light.png`,
`reports/A11_map_redirect.png`.

## Прогон

| Что | Результат |
|---|---|
| `pytest -q` (полный) | `1965 passed, 24 skipped, 1 warning in 613.44s (0:10:13)` — 0 failed |
| `pytest -q tests/test_e2e_smoke.py tests/test_ui_verify.py` | `2 passed in 40.48s` (после правки скриптов) |
| pre-commit hook | `1772 passed, 217 deselected` + пересборка sitemap/feed — OK |
| Коммит | `b14a504f` — 15 файлов (+116/−48), из них `docs/sitemap.xml` пересобран хуком |
| Пуш | `a9fbb3f5..b14a504f  v5.6.5-dev -> v5.6.5-dev` |

Единственное предупреждение прогона — `test_no_new_orphan_classes`: 43 мёртвых класса,
все уже перечислены в `KNOWN_DEAD_CSS` (список не менялся).

## Наблюдение (не правилось в этом хотфиксе)

`map.html` остался в `scripts/build_sitemap.py::ROOT_PAGES`, хотя стал редиректом.
Комментарий в генераторе sitemap говорит, что редиректы в sitemap не место (так убрали
`graph.html` и `atlas.html`). Но там же остались ещё три страницы-редиректа —
`calculator.html`, `interactions.html`, `compare.html`. Убирать только `map.html`
выборочно означало бы чинить правило наполовину; чинить его целиком — отдельная задача
вне рамок хотфикса. Отдельно: `hactar.html` в sitemap не числится вовсе (пробел с
момента H-1).
