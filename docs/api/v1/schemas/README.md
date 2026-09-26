# API Schemas - JSON Schema валидация

> Формальные [JSON Schema](https://json-schema.org/) для валидации ответов API.
> Дополняют [OpenAPI 3.0 spec](../openapi.yaml).

## Файлы

| Файл | Что описывает |
|------|---------------|
| index.schema.json | Схема для /api/v1/index.json |
| supplements.schema.json | Схема для /api/v1/supplements.json |

## Использование (Python)

```python
import json
import jsonschema
import requests

schema = json.loads(open('docs/api/v1/schemas/index.schema.json').read())
data = requests.get('https://deadsno.github.io/brain-25-evidence/api/v1/index.json').json()
jsonschema.validate(data, schema)
print('Valid')
```

## Установка зависимостей

```bash
pip install jsonschema requests
```

## Версия

- v1.0 - 2026-09-26, 2 схемы
