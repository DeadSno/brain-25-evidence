# AI_CONTEXT.md — bootstrap для нового чата

> **Прочитай целиком перед началом работы.** Обновлено: 2026-10-01 v2.0.
> Если что-то не совпадает — уточняй у пользователя, файл может отставать.

---

## 1. Что за проект

**brain-25-evidence** — открытая data-платформа о **130 биологически активных добавках** на основе 37 618 статей PubMed.

**URL:**
- Сайт: https://deadsno.github.io/brain-25-evidence/
- BI: https://brain-25-evidence.streamlit.app
- API: https://deadsno.github.io/brain-25-evidence/api/v1/index.json
- GitHub: https://github.com/DeadSno/brain-25-evidence

**Позиционирование:** хобби-проект. Не коммерция. Бесплатный. Без рекламы.
**Цель:** помочь людям выбирать БАДы на основе доказательной медицины.
**Донат:** ЮMoney https://yoomoney.ru/fundraise/1KKDKB0O1EC.260930

---

## 2. Текущее состояние

| Метрика | Значение |
|---------|:--------:|
| Карточек | 130 |
| Тестов | 143 |
| Основных HTML | 12 |
| Sup-страниц (из 130) | 5 тестовых |
| Skills в OpenCode | 15 (11 базовых + 4 deep-audit) |
| Agents | 10 |
| MCP серверов | 4 (context7, exa, playwright, duckdb) |
| Версия прода | v4.1.1 |
| Текущая ветка | **v5.0.0-dev** (всё копится там) |

---

## 3. Стек

- Backend: Python 3.11+, pandas, DuckDB, requests
- Frontend: чистый HTML/CSS/JS, без сборщиков
- Хостинг: GitHub Pages + Streamlit Cloud
- CI: GitHub Actions
- PWA: sw.js v44, manifest, офлайн
- Формы: Web3Forms (feedback.html)

---

## 4. Git workflow

- **main** — прод v4.1.1 (стабильный)
- **v5.0.0-dev** — текущая работа, всё копится там
- Один merge в main в конце — релиз **v5.0.0**

**Не создавать новые ветки** — всё в v5.0.0-dev.

---

## 5. Правила проекта

### Технические
- Коммиты — **латиница** (PowerShell ломает UTF-8)
- JSON — UTF-8 без BOM
- Не писать в data.json вручную
- **Файлы >30 строк — только через Python** (PowerShell heredoc ломает backticks)
- Ключи (Exa, Web3Forms) — **только в env-переменных**, не в конфиге

### Один трекер — ROADMAP.md
- Всё идёт в `ROADMAP.md`. **Никаких параллельных файлов** (`IDEAS.md`
  и подобных) — они создают хаос: пункт есть в двух местах, и в одном из них
  он протух.
- Техдолг, баги, флейки, отложенные правки → раздел
  **ТЕХНИЧЕСКИЙ ДОЛГ**. Обязательно к закрытию, версия проставлена.
- Новые фичи → соответствующий БЛОК / версия, а не отдельный файл-список.
- Последовательность строгая: не откладывать — закрывать.
- Исключение из правила «назначить версию» — когда **источник сам запрещает**
  это делать. Тогда пишется «требует уточнения» с цитатой источника,
  а не выдуманный срок.

### Фронтенд
- На каждой странице в `.actions` **НЕТ ссылки на саму себя**
- Футеры байт-идентичны (кроме активной ссылки)
- Тема: синхронный `html.dark` в `<head>` до style.css + `body.dark` в DCL
- Кнопка `.btn` ≥44px (WCAG 2.5.5)
- Bump `?v=N` при изменении CSS/JS
- Не использовать `scrollTo` в inline-handler (затенение) → `window.scrollTo`

---

## 6. Пользователь

**Имя:** Влад (DeadSno)
**Цель:** искать работу аналитиком (системный / data). Проект — портфолио + хобби.
**Стиль:** глубокий разбор, обоснования, без воды.
**Телефон:** Tecno CAMON 40 Premier 5G (412px CSS)
**Не хочет:** Telegram-канал, нативное приложение, платные фичи, рекламу.

---

## 7. Что сделано

- Батчи 16, 17a/b/c: 113 → **130 карточек**
- COI v4 (7.4% реальный конфликт), 6310 статей в DuckDB
- OpenAPI 3.0, 5 UML, BPMN, ERD, DMN
- Граф 1982 ребра встроен в сайт
- Feedback Web3Forms, support.html с ЮMoney
- 5 sup-страниц (kreatin, omega-3, vitamin-d, magniy, paba)
- Product Audit v1 (50 находок): 5 critical + 20 important закрыто
- 11 skills + 7 agents в OpenCode (позже +4 deep-audit skills + 3 agents)

---

## 8. Что сейчас в работе

**Ветка:** `v5.0.0-dev`
**Следующий этап:** Mobile deep audit (skill `mobile-deep-audit`)

**Порядок 6 этапов полного ревью:**
1. ✅ Product audit + 25 фиксов
2. 🔄 **Mobile deep audit** (следующий) → 17 страниц × 10 разрешений
3. ⏳ QA deep audit
4. ⏳ UI/UX deep audit
5. ⏳ Marketing deep audit
6. ⏳ Финальный merge v5.0.0

---

## 9. Ключевые ссылки

**Документация:**
- docs/dev/AI_CONTEXT.md ← этот файл
- docs/dev/ROADMAP_NEW.md — план
- reports/PRODUCT_AUDIT.md — 50 находок
- reports/AUDIT_REPORT.md — технический аудит
- .opencode/skills/SKILLS_INDEX.md — карта скиллов

**Продукт:**
- docs/data.json — 130 карточек
- data/db/brain.duckdb — SQL-база
- docs/api/v1/openapi.yaml — API-спека

---

## 10. Инструменты

**MCP (4):** context7 (docs), exa (search), playwright (browser), duckdb (SQL)
**Skills (15):** project, product, mobile-deep, ui-ux-deep, marketing-deep, qa-deep, pwa, site-navigation, data-validation, docs-sync, release-check + 4 новых
**Agents (10):** frontend-dev, mobile-dev, ux-dev, qa-dev, reviewer, data-analyst, docs-writer + 3 новых

---

## 11. Типовые проблемы

| Симптом | Фикс |
|---------|------|
| PowerShell heredoc ломает Python | Файл `_x.py` → `python _x.py` → `Remove-Item _x.py` |
| `git merge` открыл редактор | `git merge main --no-edit` |
| Mermaid backticks потерялись | `BT3 = "`" * 3` + `"\n".join(lines)` |
| Кнопка ↓ не работает | `window.scrollTo` вместо `scrollTo` |
| Тема мигает | Синхронный скрипт в `<head>` на `documentElement` |
| SW отдаёт старый файл | Bump `CACHE_VERSION` в sw.js |
| Ключ утёк | Отозвать + env-переменная + `{env:KEY}` в конфиге |

---

## 12. Начало нового чата

**Пользователь скинет:**
1. Ссылку на этот файл
2. `git branch --show-current` + `git log --oneline -5`
3. Задачу

**AI делает:**
1. Читает файл
2. Уточняет: «Этап 2 (mobile-deep-audit) не начат?»
3. Готовит план
4. Работает

**Не додумывать!** Уточнять при несоответствии.

---

## 13. Версия

- v2.0 — 2026-10-01, после product audit + 25 fixes + 4 MCP
