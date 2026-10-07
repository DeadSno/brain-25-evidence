# CyberAudit — Batch A, Skill 3/5

**Дата:** 2026-10-07
**Ветка:** v5.6-dev
**Коммит:** 11fea20
**Скилл:** cyberaudit
**Тип:** Web audit (OWASP Top 10)

---

## 1. Сводка

| Метрика | Значение |
|---------|----------|
| Тип приложения | Статический сайт (HTML/CSS/JS) |
| Сервер | Python SimpleHTTP |
| Заголовки безопасности | Отсутствуют |
| Секреты в коде | Не найдены |
| XSS защита | Корректная (esc()) |
| Обработка fetch | Корректная (.ok проверки) |
| PWA | Корректный manifest |
| Зависимости | Bootstrap 5.0.0-beta3 (устаревшая) |

**Общий статус:** Критичных уязвимостей нет. Основной риск — отсутствие заголовков безопасности.

---

## 2. P0 (критичные находки)

**P0 не найдены.**

---

## 3. P1 (важные находки)

### CYBER-P1-1: Отсутствуют заголовки безопасности

**Файл:** Серверные заголовки (http://localhost:8000/)

**Что не так:** Отсутствуют критичные заголовки безопасности:
- `Content-Security-Policy` (CSP)
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options` (защита от clickjacking)
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`

**Как воспроизвести:**
```bash
python -c "
import requests
r = requests.get('http://localhost:8000/', timeout=5)
print('Headers:', dict(r.headers))
"
```

**Рекомендация:** Добавить заголовки безопасности в серверную конфигурацию или через meta-теги в HTML.

---

### CYBER-P1-2: Bootstrap 5.0.0-beta3 — устаревшая версия

**Файл:** `docs/vendor/bootstrap-5.0.0-beta3.min.js`, `docs/vendor/bootstrap-5.0.0-beta3.min.css`

**Что не так:** Используется бета-версия Bootstrap 5.0.0-beta3 (2021 год). Эта версия содержит известные уязвимости и не получает обновлений безопасности.

**Как воспроизвести:**
```bash
Get-ChildItem docs\vendor\bootstrap* | Select-Object Name
```

**Рекомендация:** Обновить до стабильной версии Bootstrap 5.3.x или удалить, если не используется.

---

## 4. P2 (nice to have)

### CYBER-P2-1: Нет теста на заголовки безопасности

**Файл:** `tests/`

**Что не так:** Тестов на проверку заголовков безопасности нет. При добавлении заголовков легко сломать конфигурацию без обнаружения.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
test_content = ''
for f in Path('tests').glob('test_*.py'):
    test_content += f.read_text(encoding='utf-8')
if 'Content-Security-Policy' not in test_content:
    print('No CSP test found')
"
```

**Рекомендация:** Добавить тест, который проверяет наличие критичных заголовков безопасности.

---

### CYBER-P2-2: Нет теста на секреты в коде

**Файл:** `tests/`

**Что не так:** Тестов на проверку секретов в коде нет. Сейчас секретов нет, но при добавлении новых файлов легко случайно закоммитить токен или ключ.

**Как воспроизвести:**
```bash
python -c "
from pathlib import Path
test_content = ''
for f in Path('tests').glob('test_*.py'):
    test_content += f.read_text(encoding='utf-8')
if 'secret' not in test_content.lower():
    print('No secrets test found')
"
```

**Рекомендация:** Добавить тест, который сканирует код на наличие секретов (api_key, secret, password, token).

---

## 5. Что чинить в v5.6.1

1. **CYBER-P1-1:** Добавить заголовки безопасности (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
2. **CYBER-P1-2:** Обновить Bootstrap до стабильной версии или удалить
3. **CYBER-P2-1:** Добавить тест на заголовки безопасности
4. **CYBER-P2-2:** Добавить тест на секреты в коде

---

## 6. Проверенные аспекты безопасности

### 6.1 XSS защита

**Статус:** OK

Функция `esc()` в `docs/script.js:1-5` и `docs/science2.js:9-13` корректно экранирует все спецсимволы HTML:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&#39;`

Все вызовы `innerHTML` используют `esc()` для пользовательских данных.

### 6.2 Обработка ошибок fetch

**Статус:** OK

Все критичные вызовы `fetch()` проверяют `.ok`:
- `docs/script.js:184`: `if (!r.ok) throw new Error('no data for ' + url)`
- `docs/tracker.js:15`: `if (!r.ok) throw new Error('data.json HTTP ' + r.status)`
- `docs/science2.js:85,121`: `.then(r => (r.ok ? r.json() : Promise.reject(...)))`
- `docs/version.js:26`: `if (!r.ok) throw new Error('version.json HTTP ' + r.status)`

### 6.3 Секреты в коде

**Статус:** OK

Секретов в коде не найдено. Проверены:
- `docs/*.js`
- `docs/*.html`
- `scripts/*.py`
- `*.json`
- `*.md`

### 6.4 Валидация форм

**Статус:** OK

Форма обратной связи (`docs/feedback.html`) имеет:
- `required` на всех полях
- `minlength="3"` на topic
- `minlength="10"` на message
- `maxlength="120"` на topic
- `maxlength="2000"` на message
- `maxlength="200"` на email
- `type="email"` на email
- Обязательный чекбокс согласия

### 6.5 PWA

**Статус:** OK

- `docs/manifest.webmanifest` корректный
- `docs/sw.js` использует `resp.ok` проверки
- Кэширование настроено корректно

### 6.6 Зависимости

**Статус:** Частично OK

| Библиотека | Версия | Статус |
|------------|--------|--------|
| Bootstrap | 5.0.0-beta3 | Устаревшая (бета) |
| Chart.js | 4.4.1 | Актуальная |
| vis-network | 9.1.9 | Актуальная |

---

## 7. OWASP Top 10 2023 Compliance

| Категория | Статус | Примечание |
|-----------|--------|------------|
| A01: Broken Access Control | PASS | Нет серверной части |
| A02: Cryptographic Failures | PASS | Нет данных пользователей |
| A03: Injection | PASS | Нет SQL/NoSQL/Command injection |
| A04: Insecure Design | PASS | Статический сайт |
| A05: Security Misconfiguration | PARTIAL | Отсутствуют заголовки безопасности |
| A06: Vulnerable Components | PARTIAL | Bootstrap 5.0.0-beta3 |
| A07: Auth Failures | PASS | Нет аутентификации |
| A08: Data Integrity Failures | PASS | Нет серверной части |
| A09: Logging Failures | PASS | Нет серверной части |
| A10: SSRF | PASS | Нет серверной части |

---

## 8. Заключение

- **P0:** 0
- **P1:** 2 (отсутствуют заголовки безопасности, устаревший Bootstrap)
- **P2:** 2 (нет теста на заголовки безопасности, нет теста на секреты)

**Общий статус:** Критичных уязвимостей нет. XSS защита и обработка ошибок в порядке. Основной риск — отсутствие заголовков безопасности и устаревшая версия Bootstrap.
