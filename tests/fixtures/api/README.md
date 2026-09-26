# API Fixtures — mock-данные для тестов

Маленькие (3 карточки) мок-версии API-ответов для интеграционных тестов.
Не зависят от production — можно тестировать без сети.

## Файлы

| Файл | Что содержит |
|------|--------------|
| index.json | 3 карточки в метаданных |
| supplements.json | 3 полные карточки |
| errors.json | Примеры ответов при ошибках (404, 500, empty) |

## Использование

```python
import json
from pathlib import Path

FIXTURES = Path('tests/fixtures/api')
idx = json.loads((FIXTURES / 'index.json').read_text(encoding='utf-8'))
assert idx['count'] == 3
```

## Версия

- v1.0 — 2026-09-26, 3 карточки, 3 сценария ошибок
