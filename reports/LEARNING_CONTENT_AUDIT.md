# Аудит учебного конспекта .opencode/System Analysis low.md. Дата: 28.10.2026. HEAD: 56499ff9.

Объект аудита: `.opencode/System Analysis low.md` (учебный конспект системного/бизнес-аналитика, ~419 строк).
Это НЕ фикс B-находок. Код (`docs/`, `scripts/`, `tests/`, `templates/`) не троган. `AUDIT_MASTER_v565_FINAL.md`, `release/v5.6.5`, `main`, теги, прод не тронуты.

---

## 0. Проверка утечки и .gitignore

- `git check-ignore -v ".opencode/System Analysis low.md"` — пусто (файл НЕ был скрыт .gitignore).
- `git ls-files ".opencode/System Analysis low.md"` — пусто (файл не в индексе, не закоммичен).
- Вывод: файл был **untracked и не защищён .gitignore** — при `git add .` утекал бы в публичный репо.
- Действие: добавлено правило в `.gitignore` (в рабочей копии, не коммитится этим отчётом):
  ```
  # Учебный конспект СА — внутренние учебные заметки, не для публичного репо
  .opencode/System Analysis low.md
  ```
  Владельцу рекомендуется закоммитить `.gitignore` отдельным коммитом.
- `git ls-files ".opencode/skills/" | head -5` — на месте: `.opencode/skills/CONVENTIONS.md`, `SKILLS_INDEX.md`, `accessibility-check/SKILL.md`, `core-web-vitals/SKILL.md`, `data-audit/SKILL.md`. Всего 21 файл (19 скиллов + индекс-файлы). `.opencode/skills/` НЕ закрыт .gitignore — скиллы остаются в репо.

---

## 1. Самодостаточность

Подтверждаю: в конспекте **нет ссылок на текущий продукт** `brain-25-evidence`, а также нет вхождений `deadsno`, `localhost`, `:8000`.

Также нет ссылок на внешние материалы без контекста («см. статью», «подробнее тут»). Упоминания стандартов (ISO 25010, BABOK, ГОСТ 19.201-78/34.602-89, OpenAPI 3.1, SQL:1999, SQL-92) носят справочный характер и не требуют ссылок для конспекта.

Примеры в конспекте носят общий характер (доставка еды, банковские переводы, Яндекс.Карты как пример API) — не привязаны к продукту репо.

---

## 2. Таблица находок

| ID | Крит. | Раздел | Что именно | Рекомендация |
|----|-------|--------|------------|--------------|
| LEARN-01 | C | ISO 25010 / Часть 2 | Упомянута только характеристика «Функциональность» (одна из 8). Остальные 7 (производительность, совместимость, удобство использования, надёжность, безопасность, сопровождаемость, переносимость) не раскрыты. | Добавить краткое описание всех 8 характеристик ISO 25010 с примерами НФТ. |
| LEARN-02 | B | BABOK / Часть 2 | BABOK упомянут только в таблице Вигерс vs BABOK. Нет техник: Event Storming, Domain Storytelling, Job Stories, Kano, WSJF, MoSCoW. | Добавить раздел «Техники сбора и анализа требований» с описанием и примерами применения. |
| LEARN-03 | B | UML 2.5.1 / Часть 3 | Только 5 из 14 диаграмм (Use Case, Sequence, Activity, Class, State Machine). Отсутствуют: Component, Deployment (для Middle критично), Package, Object, Communication, Timing, Interaction Overview, Composite Structure, Profile. | Добавить диаграммы Component и Deployment с примерами для микросервисной архитектуры. |
| LEARN-04 | B | BPMN 2.0 / Часть 3 | Пулы/дорожки/шлюзы есть. Отсутствуют: Events (start, end, intermediate, boundary, error, timer), Subprocesses, Collaboration, Choreography, Message Flows. Для Middle критично. | Добавить раздел «События и подпроцессы BPMN» с примерами boundary/timer/events. |
| LEARN-05 | B | DDD / Часть 3 | Entity, Value Object, Aggregate, Bounded Context есть. Отсутствуют: Domain Event, Repository, Factory, Anti-Corruption Layer, Context Map, Ubiquitous Language. Для Middle нужно. | Добавить тактические паттерны DDD (Repository, Factory, ACL, Context Map, Domain Event, Ubiquitous Language). |
| LEARN-06 | B | C4 / Часть 7 (В7) | C4 упомянут только кратко в ответе В7. Нет отдельного раздела и нет описания 4 уровней (Context, Container, Component, Code), нет примеров диаграмм. | Вынести C4 в отдельный раздел с описанием 4 уровней и примерами диаграмм. |
| LEARN-07 | B | API / Часть 4 | REST, SOAP, gRPC есть. Отсутствуют: GraphQL, WebSocket, AsyncAPI (для Kafka), streaming, rate limiting, pagination, versioning. | Добавить разделы по GraphQL/WebSocket/AsyncAPI, версионированию API и пагинации. |
| LEARN-08 | C | OAuth 2.1 / OIDC / Часть 5 | PKCE упомянут (вamente), но нет разницы Authorization Code vs Client Credentials, нет refresh-rotation. | Добавить сравнение OAuth flow и описание ротации refresh-токенов. |
| LEARN-09 | B | SQL / Часть 4 | Есть SELECT, JOIN, оконные (ROW_NUMBER), CTE. Отсутствуют: EXPLAIN, индексы (B-tree, hash, composite), транзакции на практике (BEGIN/COMMIT/ROLLBACK, savepoints), оконные функции детально (LAG/LEAD, RANK vs DENSE_RANK). | Добавить раздел «SQL на практике» с EXPLAIN, индексами и примерами транзакций. |
| LEARN-10 | B | Архитектура / Часть 5 | Монолит/микросервисы, Saga, Idempotency, Outbox, Circuit Breaker есть. Отсутствуют: ADR, contract testing (Pact), observability (OpenTelemetry, метрики/логи/трейсы), blue-green/canary, feature flags, CQRS, Event Sourcing. | Добавить раздел «Современная архитектура» с ADR, Observability, CQRS/Event Sourcing, feature flags. |
| LEARN-11 | B | AI 2026 / Часть 6 | Agentic AI, Data Governance есть. RAG упомянут без определения. Отсутствуют: MCP (Model Context Protocol), LLM evaluation (precision/recall, hallucination), prompt injection, guardrails. | Добавить определение RAG и раздел «Безопасность и оценка LLM» (MCP, prompt injection, guardrails, evaluation). |
| LEARN-12 | B | Безопасность / Часть 5 | OWASP Top 10 и STRIDE не упомянуты (есть только OAuth/JWT/mTLS). | Добавить раздел «OWASP Top 10 и STRIDE» с примерами угроз и мер защиты. |
| LEARN-13 | B | Тестирование / Часть 1, 5 | unit/integration/e2e, contract testing, test pyramid не упомянуты (в SDLC только этап «Тестирование» без деталей). | Добавить раздел «Тестирование» с пирамидой и видами тестирования. |
| LEARN-14 | C | Оценка задач / Часть 1 | Нет story points, planning poker, velocity. | Добавить кратко в разделе Scrum/оценка задач. |
| LEARN-15 | C | Стейкхолдеры / Часть 7 | Нет RACI. Конфликты и эскалация только частично (В3 про фичу в спринт, Agentic AI escalation paths). | Добавить матрицу RACI и приёмы разрешения конфликтов стейкхолдеров. |
| LEARN-16 | C | Орфография / стр. 15 | Опечатка: «код написалс правильно» → должно быть «написался». | Исправить опечатку. |
| LEARN-17 | C | Орфография / стр. 60 | Опечатка: «Kaban» → должно быть «Kanban». | Исправить опечатку. |
| LEARN-18 | C | Орфография / стр. 277 | Опечатка: «Prinzip» (немец. слово) → должно быть «Принцип». | Исправить на русский термин. |
| LEARN-19 | C | Орфография / стр. 412 | Опечатка: «еёwhole» → «её whole» / «целиком». | Исправить разделение слов. |
| LEARN-20 | C | Терминология / Часть 1 | Неконсистентность сокращений: «системный аналитик» vs «СА», «бизнес-аналитик» vs «БА» (иногда со скобками, иногда без). | Единообразить сокращения при первом упоминании. |

---

## 3. Сводка

- **A (грубая ошибка / устаревший факт / неверный стандарт):** 0
- **B (серьёзный пробел для Middle):** 11 (LEARN-02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13)
- **C (опечатка / мелкий пробел / стилистика):** 9 (LEARN-01, 08, 14, 15, 16, 17, 18, 19, 20)
- Всего находок: 20

Грубых ошибок (A) не выявлено — конспект содержит корректную базовую информацию. Основная проблема — значительные пробелы для уровня Middle (B) в моделировании, архитектуре, безопасности и тестировании.

---

## 4. Оценка готовности

Конспект покрывает Junior/Middle примерно на **65–70%** (субъективная оценка по разделам):

| Раздел | Покрытие | Комментарий |
|--------|----------|-------------|
| Фундамент (роль, SDLC, методологии) | ~85% | Сильно: роль, SDLC, Waterfall/Scrum/Kanban, DoR/DoD/AC. Слабо: story points, planning poker, velocity. |
| Требования (Вигерс, BABOK,トラсировка) | ~70% | Хорошая таблица Вигерс vs BABOK, переходные требования. Но нет техник сбора (Event Storming, Kano, MoSCoW и др.). |
| Моделирование (BPMN, UML, DDD) | ~60% | Есть базовые диаграммы UML (5/14) и BPMN (пулы/шлюзы). Нет Component/Deployment UML, BPMN Events, тактики DDD (Repository, ACL, Context Map). |
| API / БД (SQL) | ~65% | REST/SOAP/gRPC, OpenAPI 3.1, SQL базовый (SELECT/JOIN/оконные/CTE). Нет GraphQL/WebSocket/AsyncAPI, индексов, EXPLAIN, транзакций на практике. |
| Архитектура | ~55% | Saga/Idempotency/Outbox/Circuit Breaker есть. Нет ADR, Observability (OpenTelemetry), CQRS/Event Sourcing, feature flags, blue-green/canary. |
| Интервью (топ-10, Часть 7) | ~75% | Эталонные ответы В1–В10 хорошие для Junior, но поверхностные для Middle (нет C4 примеров, story points, конфликтов стейкхолдеров в глубине). |

Итоговый вывод: конспект надёжен какJunior-справочник, но для уровня Middle требует доработки по B-находкам прежде чем считаться полным руководством к подготовке.

---

## 5. Что добавить в первую очередь (топ-5 по критичности)

1. **BPMN 2.0 Events и Subprocesses** (start/end/intermediate/boundary/error/timer, Message Flows) — критично для Middle (LEARN-04).
2. **UML Component и Deployment диаграммы** — архитектурное моделирование для Middle (LEARN-03).
3. **C4 — отдельный раздел с 4 уровнями и примерами диаграмм** (LEARN-06).
4. **Observability (OpenTelemetry) + ADR + CQRS/Event Sourcing** — современная архитектура (LEARN-10).
5. **Тестирование: пирамида, unit/integration/e2e, contract testing** (LEARN-13).

---

## 6. Подтверждения

- Код (`docs/`, `scripts/`, `tests/`, `templates/`) **не тронут**.
- `AUDIT_MASTER_v565_FINAL.md` **не тронут**.
- Ветка `release/v5.6.5` **не тронута**. Ветка `main` **не тронута**. Теги **не ставились**. Прод **не затрагивался**.
- Отчёт `reports/LEARNING_CONTENT_AUDIT.md` — внутренний документ, не публикуется на Pages. `reports/` не в `.gitignore` (исключены только отдельные файлы/паттерны, не каталог целиком), отчёт можно закоммитить отдельным коммитом.
