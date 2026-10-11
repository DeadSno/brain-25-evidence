# TEST_UI_VERIFY.md — проверка test_ui_verify.py

## 1. Есть ли screenshot в test_ui_verify
- Нет. В tests/test_ui_verify.py нет вызовов screenshot().

## 2. Маскируется ли версия
- Нет. В tests/test_ui_verify.py нет кода для маскировки версии (data-version, mask).

## 3. Рекомендация
- test_ui_verify.py не делает скриншотов, поэтому маскировка версии не требуется.
- Если в будущем в test_ui_verify.py будут добавлены скриншоты, нужно применить ту же маску, что в test_visual_snapshots.py:
  ```javascript
  document.querySelectorAll('[data-version="app"]').forEach(el => {
      el.textContent = 'vX.X.X';
  });
  ```
- Это предотвратит расхождения в визуальных тестах при смене версии.
