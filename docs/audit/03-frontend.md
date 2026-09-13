# AUDIT C (S4) — фронтенд
Дата: 2026-09-13 | скрипт: scripts/audit_frontend.py | файлы НЕ менялись

## Шапка
| Severity | Кол-во |
| --- | --- |
| 🔴 | 1 |
| 🟡 | 8 |
| 🟢 | 0 |

## Топ-5
- 🔴 **fetch-ошибки**: map.html: fetch БЕЗ проверки r.ok и БЕЗ .catch() — 404/500/битый JSON = белый экран (нет видимого сообщения)  `docs/map.html:115`
- 🟡 **XSS-векторы**: innerHTML собирает разметку из полей data.json и НЕТ хелпера экранирования (data.json first-party => 🟡, не 🔴): 10 sinks  `script.js:18: $('cardsGrid').innerHTML = h;; script.js:24: .catch(() => { document.body.innerHTML = '<p style="color:red">❌ Не удалось загр; script.js:114: if (!data.length) { g.innerHTML = '<p style="opacity:.6">Ничего не найдено — поп; script.js:115: g.innerHTML = data.map(s => '<div class="card" data-id="' + s.id + '">' +; script.js:148: $('modalBody').innerHTML = '<h2>' + s.name + '</h2>' +; script.js:177: calcResult.innerHTML = html;`
- 🟡 **fetch-ошибки**: map.html: нет ни одного .catch()  `docs/map.html`
- 🟡 **localStorage**: theme в script.js читается БЕЗ try/catch (localStorage может кидать SecurityError в приватном режиме) — упадёт инициализация  `docs/script.js:28`
- 🟡 **a11y**: модалка без role=dialog/aria-modal и без фокуса-трапа  `docs/index.html:114-118`

## Инфо
- innerHTML-sinks (все строки исполняют разметку из data.json — first-party):
- векторы пользователя: #sup= и ?supplement= валидируются через `SUPS.some(s=>s.id===x)` перед рендером — инъекции нет.
- countBadge/статистика используют textContent — безопасно.
- script.js: fetch с проверкой r.ok + `.catch()` → видимое сообщение при 404/500/битом JSON.
- Chart.js: destroy() перед пересозданием bubble- и radar-графиков — утечек нет.
- Chart.js подключён один раз (cdn v4.4.1); собственные канвасы destroy корректно.
- d3 не подключён и не используется — остатков нет.
- localStorage: index.html=1 обращений, map.html=4, script.js=4.
- getFavs(): JSON.parse обёрнут в try/catch → битые fav="{{{" → [] — ок.
- mapClosed: JSON.parse обёрнут в try/catch → битые значения отфильтрованы — ок.
- theme в index.html <head> читается в try/catch — ок.
- Esc закрывает модалку (script.js) и сбрасывает поиск (map.html) — ок.
- медиа-запросы: style.css(768px) и map.html(860px) есть; 375px-ветка в любом случае схлопывается — глазами не прогонялась (playwright не установлен).
- примечание: визуальную проверку 375px нельзя выполнить headless (playwright не установлен) — нужна проверка человеком.
- data.json=65854 байт (64.3 КБ) — для 81 карточки приемлемо; рендер 81 карточки O(n) без сет-расчётов; Chart.js cdn 4.4.1.
- шрифт Inter: preconnect к googleapis+gstatic есть — ок (перф).

## Находки (≤25)
🟡 XSS-векторы: innerHTML собирает разметку из полей data.json и НЕТ хелпера экранирования (data.json first-party => 🟡, не 🔴): 10 sinks  `script.js:18: $('cardsGrid').innerHTML = h;; script.js:24: .catch(() => { document.body.innerHTML = '<p style="color:red">❌ Не удалось загр; script.js:114: if (!data.length) { g.innerHTML = '<p style="opacity:.6">Ничего не найдено — поп; script.js:115: g.innerHTML = data.map(s => '<div class="card" data-id="' + s.id + '">' +; script.js:148: $('modalBody').innerHTML = '<h2>' + s.name + '</h2>' +; script.js:177: calcResult.innerHTML = html;`
🔴 fetch-ошибки: map.html: fetch БЕЗ проверки r.ok и БЕЗ .catch() — 404/500/битый JSON = белый экран (нет видимого сообщения)  `docs/map.html:115`
🟡 fetch-ошибки: map.html: нет ни одного .catch()  `docs/map.html`
🟡 localStorage: theme в script.js читается БЕЗ try/catch (localStorage может кидать SecurityError в приватном режиме) — упадёт инициализация  `docs/script.js:28`
🟡 a11y: модалка без role=dialog/aria-modal и без фокуса-трапа  `docs/index.html:114-118`
🟡 a11y: кнопка закрытия модалки без aria-label/aria-hidden (двойной таб не сообщит смысл)  `docs/index.html:116`
🟡 a11y: категории карты — <h3>/<span>, не фокусируемые (только клик; клавиатура не дойдёт)  `docs/map.html:126-127`
🟡 a11y: контраст бейджа вердикта v0 (#f1c40f + белый текст) ~1.9:1 < 4.5:1 (WCAG AA не проходит)  `docs/style.css:161`
🟡 a11y: контраст бейджа v1 (#2ecc71 + белый текст) ~2.1:1 < 4.5:1  `docs/style.css:160`
