# Fallback Plugin Installation Report

## 1. Версия OpenCode
**v1.18.33** (v1)

## 2. Был ли уже fallback-плагин
**Нет**, fallback-плагин отсутствовал.

## 3. Что добавлено в opencode.jsonc (точный diff)
```diff
-  "plugin": ["opencode-team-lead"],
+  "plugin": ["opencode-team-lead", "@azumag/opencode-rate-limit-fallback@1.70.11"],
```

## 4. Что создано в rate-limit-fallback.json
```json
{
  "enabled": true,
  "cooldownMs": 60000,
  "fallbackMode": "cycle",
  "maxSubagentDepth": 10,
  "enableSubagentFallback": true,
  "fallbackModels": [
    { "providerID": "opencode", "modelID": "longcat-2.5-preview-free" }
  ],
  "retryPolicy": {
    "maxRetries": 3,
    "strategy": "exponential",
    "baseDelayMs": 1000,
    "maxDelayMs": 30000,
    "jitterEnabled": true,
    "jitterFactor": 0.1
  }
}
```

## 5. Точное имя модели Longcat
**`longcat-2.5-preview-free`** (providerID: `opencode`)

## 6. Путь к конфигу плагина
Создано в обоих возможных путях:
- `C:\Users\TshK\.opencode\rate-limit-fallback.json`
- `C:\Users\TshK\.config\opencode\rate-limit-fallback.json`

## 7. Что требуется перезапуск OpenCode
**ДА**, требуется полный перезапуск OpenCode для загрузки плагина.

## 8. Вопросы владельцу
- Какой из двух путей конфигурации использует плагин? (`.opencode` или `.config\opencode`)
- Нужно ли удалить один из дублирующих файлов конфигурации после проверки?
