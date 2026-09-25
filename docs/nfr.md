# НФТ — нефункциональные требования

> Нефункциональные требования (НФТ) описывают **КАК** система работает,
> в отличие от функциональных требований (User Stories), описывающих **ЧТО** она делает.

## 1. Производительность

### 1.1 API
| Метрика | Требование | Обоснование |
|---------|-----------|-------------|
| Latency `index.json` | < 200 ms (p95) | Малый размер (< 5 KB), CDN |
| Latency `supplements.json` | < 800 ms (p95) | 660 KB, CDN + gzip |
| Throughput | > 1000 req/s | GitHub Pages CDN |
| Размер ответа | index < 5 KB, supplements < 1 MB | Кэшируется браузером |

### 1.2 UI
| Метрика | Требование |
|---------|-----------|
| First Contentful Paint | < 1.5 s |
| Time to Interactive | < 2.5 s |
| Поиск (debounce 300 ms) | < 100 ms локально |
| Фильтрация | < 50 ms |

### 1.3 Сбор данных (ETL)
| Задача | Норматив |
|--------|----------|
| Fetch метаданных (37 618 papers) | < 10 мин |
| Fetch full texts (11 940 XML) | < 60 мин |
| Enrich карточек (130 шт) | < 5 мин |
| Полный pipeline | < 2 часа |

## 2. Масштабируемость

| Параметр | Текущее | Предел | Действие при достижении |
|----------|---------|--------|--------------------------|
| Карточек в data.json | 130 | 5 000 | Миграция на PostgreSQL |
| Размер data.json | 76 KB | 5 MB | Разбить на шарды |
| Full texts | 11 940 | 100 000 | S3 + lazy load |
| Пользователей API | ~0 (публичный) | 10 000/день | CDN + rate limit |

## 3. Доступность (SLA)

| Компонент | SLA | Downtime/мес |
|-----------|-----|--------------|
| GitHub Pages | 99.9% | 43 мин |
| Streamlit Cloud | 99.5% | 3.6 ч |
| Внешние API (PubMed, EBI) | Best effort | Не SLA |

**Реакция на сбой:**
- GitHub Pages недоступен → статика на CDN продолжает работать
- Streamlit недоступен → fallback на GitHub Pages
- PubMed API недоступен → retry 3× с backoff

## 4. Безопасность

### 4.1 Данные
- **Никаких PII** — публичные данные о добавках
- **No secrets в коде** — email в API передаётся через env
- **HTTPS only** — enforced GitHub Pages
- **CSP headers** — GitHub Pages по умолчанию

### 4.2 API
- **No auth** — публичный read-only
- **No write** — только GET endpoints
- **Rate limiting** — GitHub Pages не предоставляет; при росте → Cloudflare
- **CORS** — `*` (публичные данные)

### 4.3 Зависимости
- **Dependabot** — автообновление
- **pip-audit** — проверка уязвимостей (запланировано)
- **pytest** — 118 тестов, CI блокирует merge при FAIL

## 5. Совместимость

### 5.1 Браузеры (UI)
| Браузер | Минимум |
|---------|---------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

**Причина:** использование `Intl`, `fetch`, `IntersectionObserver`.

### 5.2 Python
| Версия | Поддержка |
|--------|-----------|
| 3.11 | ✅ Primary |
| 3.12 | ✅ CI |
| 3.13 | ✅ CI |
| 3.10 | ⚠️ Deprecated |

### 5.3 API
- **Content-Type:** `application/json; charset=utf-8`
- **Кодировка:** UTF-8 без BOM
- **Схема:** OpenAPI 3.0.3

## 6. Удобство использования (Usability)

| Требование | Обоснование |
|-----------|-------------|
| Мобильная адаптация | Responsive design, 320px+ |
| Тёмная тема | Автоматически через `prefers-color-scheme` |
| Клавиатурная навигация | Tab, Enter, Esc |
| ARIA-разметка | Screen readers |
| Язык | Русский (приоритет), англ. термины |

## 7. Сопровождаемость

| Метрика | Требование |
|---------|-----------|
| Покрытие тестами | > 80% (сейчас: pytest 118 тестов) |
| Покрытие docs | 100% публичных функций (docstrings) |
| Время setup | < 5 мин (clone → run) |
| Язык документации | Русский |
| Commit messages | Латиница (PowerShell UTF-8 bug) |

## 8. Наблюдаемость (Observability)

| Компонент | Инструмент |
|-----------|-----------|
| Tests | pytest + GitHub Actions |
| Логи ETL | stdout, файлы в `reports/` |
| Метрики покрытия | badges в README |
| Snapshot-тесты | `tests/snapshot_data.json` |
| Версионирование | semver (v3.7.0) |

## 9. Совместимость с инструментами аналитика

| Инструмент | Поддержка |
|-----------|-----------|
| Excel | Прямая загрузка CSV-экспорта |
| pandas | JSON читается `pd.read_json` |
| Power BI | REST API connector |
| Tableau | Web Data Connector (JSON) |
| SQL | DuckDB/PostgreSQL схема в `scripts/db/` |

## 10. Правовые и лицензионные требования

| Требование | Статус |
|-----------|--------|
| Лицензия данных | CC BY 4.0 |
| Лицензия кода | MIT (см. LICENSE) |
| Источники данных | PubMed (public), Europe PMC (Open Access) |
| Attribution | Обязательна при использовании |
| GDPR | Не применимо (нет PII) |

## Матрица приоритетов (MoSCoW)

| Категория | Must | Should | Could | Won't (v1) |
|-----------|------|--------|-------|-------------|
| Производительность | Latency < 800 ms | p95 метрики | Real-time | — |
| Масштабируемость | До 5 000 карточек | Шардирование | Автошард | — |
| Доступность | 99.9% статика | Мониторинг | — | SLA-контракты |
| Безопасность | HTTPS, no PII | Rate limit | OAuth | Хранение PII |
| Совместимость | Chrome/Firefox/Safari | Edge | IE11 | — |

## Версия

- v1.0 — 2026-09-25, batch 17c, 130 добавок, 11 940 full texts
