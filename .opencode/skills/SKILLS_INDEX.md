# SKILLS_INDEX — карта всех скиллов

> Куда смотреть: какой скилл использовать в какой ситуации.
> Обновлено: 2026-10-02. **Скиллов: 18.**

## Порядок применения для полного ревью

Порядок — по приоритету применения, а не по происхождению скилла: внешние
(cyberaudit, accessibility-check, seo-check, core-web-vitals, i18n-rtl-audit)
стоят там, где они бьют по общему фундаменту.
Установлены 2026-10-02, см. `reports/SKILLS_INSTALL.md`.

1. **project-audit** — архитектура и структура
2. **data-validation** — корректность данных
3. **cyberaudit** — безопасность (OWASP Top 10, секреты, API)
4. **data-audit** — полный аудит данных в 5 слоёв (заменил `data-quality-auditor` 2026-10-03)
5. **docs-sync** — синхронизация документации
6. **product-audit** — быстрый обзор UI/UX + marketing + QA + mobile
7. **visual-design-audit** — цветокор, типографика, отступы, тени, темы
8. **ui-ux-deep-audit** — состояния, иерархия, микроинтеракции
9. **accessibility-check** — WCAG 2.1 A/AA: контраст, alt, клавиатура, ARIA
10. **mobile-deep-audit** — глубокая мобильная адаптация (10 разрешений)
11. **marketing-deep-audit** — воронка, CTA, соцдоказательства
12. **seo-check** — meta, OG, canonical, JSON-LD, robots/sitemap
13. **qa-deep-audit** — покрытие, edge cases, error handling
14. **core-web-vitals** — LCP/CLS и бюджет веса страницы
15. **pwa-audit** — PWA-спецификация
16. **site-navigation** — единый набор кнопок и навигации
17. **i18n-rtl-audit** — локализация и RTL (перед v5.3)
18. **release-check** — перед коммитом

Порядок не случаен: сначала структура, данные и безопасность (дешёвое, ломает
всё остальное), затем визуал и поведение, в конце PWA и навигация, и только
потом release-check — он имеет смысл, когда остальные уже отработали.

## Скиллы по назначению

### Аудит и диагностика
| Скилл | Что делает | Когда вызывать |
|-------|-----------|----------------|
| project-audit | Архитектура, зависимости, мёртвый код | Раз в месяц или после крупной фичи |
| product-audit | Быстрый обзор 4 направлений | После релиза |
| visual-design-audit | Цвет, шрифты, отступы, тени, темы, метрики | После правок style.css |
| mobile-deep-audit | Мобильная адаптация 10 разрешений | После каждого изменения CSS/HTML |
| ui-ux-deep-audit | Иерархия, состояния, микроинтеракции | Когда «что-то не так» в UI |
| marketing-deep-audit | Воронка, CTA, тексты | Раз в квартал |
| qa-deep-audit | Покрытие, edge cases | После новой фичи |
| pwa-audit | PWA спецификация | После изменения sw.js / manifest |
| data-validation | data.json, effect_tags, БД | После batch добавления карточек |
| data-audit | 5 слоёв: data.json, производные, DuckDB, сырые, внешний | Когда нужен полный аудит данных, а не только корректность |
| docs-sync | Синхронизация документации | После правок docs/ |
| release-check | Готовность к коммиту | Перед каждым push |
| site-navigation | Единый набор кнопок | После правки навигации |

### Установленные 2026-10-02 (внешние)
| Скилл | Что делает | Источник | Когда вызывать |
|-------|-----------|----------|----------------|
| cyberaudit | OWASP Top 10, секреты в коде, API/web/mobile/cloud. **Покрывает и security-audit, и api-audit** | `cyberaudit-skill@3.2.1` | Перед релизом, при работе с внешним вводом |
| accessibility-check | WCAG 2.1 A/AA: контраст, alt, заголовки, клавиатура, ARIA, фокус | `Quality-Max/free-qa-skills` | После любой вёрстки; обязательно перед релизом |
| seo-check | meta/OG, canonical, JSON-LD, robots.txt, sitemap | `Quality-Max/free-qa-skills` | При изменении `<head>` или структуры страниц |
| core-web-vitals | LCP/CLS, вес страницы, ленивая загрузка, third-party | `Quality-Max/free-qa-skills` | Перед релизом; при жалобах «медленно» |
| i18n-rtl-audit | Локализация, RTL, lang-атрибуты | `Quality-Max/free-qa-skills` | **Перед v5.3** — до того локализации нет |

> `data-quality-auditor` (`alirezarezvani/claude-skills`) удалён 2026-10-03,
> заменён на `data-audit`. Причина: работал только с CSV, а на нашем
> `docs/data.json` читал его как плоский текст — DQS 97/100 на таком входе
> бессмысленен.

### Границы между скиллами

Три скилла смотрят на интерфейс, и их легко перепутать:

| Вопрос | Кто отвечает |
|---|---|
| «Какого размера шрифт и какие цвета» | visual-design-audit |
| «Что показано, пока данных нет» | ui-ux-deep-audit |
| «Кнопка меньше пальца, safe-area, контраст AA» | mobile-deep-audit |
| «Кликабельно ли в воронке, понятен ли текст» | marketing-deep-audit |
| «Тот грейд значит то, что кажется?» | product-audit |

Новые скиллы перекрываются с существующими — важно не запускать оба:

| Вопрос | Кто отвечает |
|---|---|
| «Контраст / alt / клавиатура» | **accessibility-check**, а не mobile-deep-audit |
| «Кнопка меньше пальца, safe-area» | mobile-deep-audit (touch target), accessibility-check (если это WCAG-критерий) |
| «data.json корректен» | **data-validation** (умеет JSON + DuckDB) |
| «полный аудит данных по всем слоям» | **data-audit** (5 слоёв, один отчёт) |
| «выбросы и аномалии в числах» | **data-audit**, слой 1 (3σ) и слой 3 |
| «meta / canonical / JSON-LD» | seo-check, а не docs-sync |
| «Core Web Vitals, вес страницы» | core-web-vitals |
| «секрет в коде, XSS, CSRF» | cyberaudit |
| «дублируется CSS, мёртвые зависимости» | project-audit (cyberaudit тоже ловит `npm audit`) |

### Известные ограничения новых скиллов

1. **`data-audit` требует доступа к DuckDB, а файл может быть занят.**
   `data/db/brain.duckdb` держит рабочий процесс (в нашей среде — `node.exe`),
   и тогда `duckdb.connect(..., read_only=True)` падает с `WinError 32`, а
   `shutil.copy2` — тоже. Запрашивать БД через MCP `query_duckdb`: он открывает
   файл read-only и работает при занятой копии.
2. **Скрипты, печатающие эмодзи, не работают в консоли Windows** без
   `$env:PYTHONIOENCODING="utf-8"`: cp1251 их не кодирует.
3. **`accessibility-check` требует Playwright MCP**; в этом окружении доступен
   `playwright`-сервер, MCP-имя в скилле может отличаться.
4. **`cyberaudit` — 131 файл, 556 КБ.** Установлен и глобально
   (`~/.config/opencode/skills/`), и в репозитории. Глобальная копия старее
   (v3.1.5 против v3.2.1 в репозитории).

### Отложенные скиллы

| Скилл | Статус | Причина |
|---|---|---|
| llm-security-audit (`dacuma-labs/agent-security-audit`) | Найден, **не установлен** | Его собственный description: «Do NOT use for: projects with no agentic components». У нас статический сайт без агентов. Ставить перед v6.0, когда появятся LLM-компоненты |
| i18n-audit (собственный) | Не нужен | Готовый `i18n-rtl-audit` уже стоит; писать свой не требуется |

### Внешний инструмент (не скилл)

| Инструмент | Что делает | Как запускать |
|---|---|---|
| vortix-cli | Статический аудит сайта: performance, security, accessibility, bugs, seo, maintainability, privacy. Считает оценку 0-100 и грейд A-F | `npx -y vortix-cli@0.1.3 check` |

Конфиг: `.vortix/config.json` (`outputDir: docs`, `build: false`, категории:
performance, security, accessibility, bugs, seo, maintainability, privacy). **Это CLI, а не скилл** — агентом он сам не вызывается, его
надо запускать вручную и читать вывод.

При первом прогоне на 2026-10-02: **77/100, Grade C**, 18 страниц,
338 errors / 26 warnings / 38 notices; хуже всего accessibility и bugs.

### По триггерам

**«Что-то сломалось»:**
- project-audit → product-audit → mobile-deep-audit

**«Готовим релиз»:**
- release-check → cyberaudit → accessibility-check → seo-check →
  core-web-vitals → data-validation → docs-sync → product-audit

**«Пользователь жалуется на мобилку»:**
- mobile-deep-audit → pwa-audit

**«Плохо конвертит»:**
- marketing-deep-audit → ui-ux-deep-audit

**«Боимся багов»:**
- qa-deep-audit → project-audit

**«Выглядит несолидно / стыдно смотреть»:**
- visual-design-audit → ui-ux-deep-audit

**«Жалобы на скорость»:**
- core-web-vitals → project-audit

**«Приёмка на безопасность»:**
- cyberaudit (web) → cyberaudit (api) → secret-scan при необходимости

## Правила использования

1. **Один скилл — одно направление.** Не смешивать.
2. **Только чтение** — скилл не меняет файлы.
3. **Один отчёт** на запуск (в reports/).
4. **Единый лимит находок — ориентир 60.** При превышении группировать однотипные (130 звёзд = 1 находка), P0/P1 не резать никогда, P2 сжимать до паттернов. Число в отчёте — что нашлось, а не что влезло. Формулировка одинакова во всех скиллах, см. раздел «Лимит находок» в SKILL.md.
5. **После отчёта — обсудить, потом фиксить.**
6. **Находка без воспроизведения не считается находкой.** Правило и почему —
   в каждом SKILL.md, раздел «Правило верификации находок».
7. **Внешний скилл — не значит проверенный.** `cyberaudit`, `seo-check`,
   `core-web-vitals` пришли из чужих репозиториев; их находки проходят то же
   правило верификации, что и наши.

## Команды

```bash
pytest -q                     # все тесты (736 passed, 18 skipped)
pytest -q tests/test_api_contract.py       # контракт API
pytest -q -m e2e              # браузерные e2e, требует RUN_E2E=1
RUN_SNAPSHOTS=1 pytest -q -m snapshots      # визуальные снапшоты, 37 шт.
node --check docs/script.js   # синтаксис JS без сборщиков
python scripts/ui_verify.py   # браузерная проверка UI
npx -y vortix-cli@0.1.3 check # внешний статический аудит сайта
```

`pytest -q -m "not network"` — **устаревшая команда**. Метка `network` удалена
2026-10-01: сетевых тестов в проекте нет, фильтр ничего не исключал.

## Агенты (для фиксов, не для аудита)

| Агент | Что делает |
|-------|-----------|
| frontend-dev | HTML/CSS/JS правки |
| mobile-dev | Мобильная адаптация |
| ux-dev | Состояния UI, микроинтеракции |
| qa-dev | Тесты, edge cases |
| reviewer | Ревью кода |
| data-analyst | SQL, DuckDB, данные |
| docs-writer | Документация |

Агенты тоже соблюдают «Правило верификации находок» — блок есть в каждом из них.

## Реестр отчётов

| Скилл | Отчёт |
|---|---|
| project-audit | reports/AUDIT_REPORT.md |
| product-audit | reports/PRODUCT_AUDIT.md |
| visual-design-audit | reports/VISUAL_DESIGN_AUDIT.md |
| ui-ux-deep-audit | reports/UI_UX_AUDIT.md |
| mobile-deep-audit | reports/MOBILE_AUDIT.md |
| qa-deep-audit | reports/QA_AUDIT.md |
| ревизия скиллов | reports/SKILLS_REVISION.md |
| установка скиллов | reports/SKILLS_INSTALL.md |

## Полный список (18)

- accessibility-check
- core-web-vitals
- cyberaudit
- data-audit
- data-validation
- docs-sync
- i18n-rtl-audit
- marketing-deep-audit
- mobile-deep-audit
- product-audit
- project-audit
- pwa-audit
- qa-deep-audit
- release-check
- seo-check
- site-navigation
- ui-ux-deep-audit
- visual-design-audit

**Версия:** v2.0 (2026-10-02)
