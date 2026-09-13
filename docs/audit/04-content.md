# AUDIT D (S2) — тексты, термины, числа, даты, ссылки
Дата: 2026-09-13 | скрипт: scripts/audit_content.py | файлы НЕ менялись

## Шапка
| Severity | Кол-во |
| --- | --- |
| 🔴 | 5 |
| 🟡 | 5 |
| 🟢 | 0 |

## Топ-5
- 🔴 **числа 41/81**: устаревшее «41» в UI/описаниях: 4 шт  `docs/index.html:20: 41 добав; docs/index.html:20: — 41; docs/script.js:39: 41 добав; docs/script.js:39: — 41`
- 🔴 **числа 41/81**: README-бейдж supplements => 41 (а data.json=81)  `README.md:9`
- 🔴 **числа 41/81**: README-бейдж version => v1.2 (текущий v2.0)  `README.md:8`
- 🔴 **числа 41/81**: README-бейдж tests => 17 passed (сейчас 24+1 deselected)  `README.md:10`
- 🔴 **дисклеймер**: на docs/map.html дисклеймера на странице нет  `docs/map.html`

## Инфо
- термин «вердикт»: UI=2, data.verdict=0 (index/map/script).
- термин «статус» в UI/данных НЕ встречается (альтернатива «вердикту»?): согласовано.
- термин «ценность»: UI=3, data.verdict=0 (index/script).
- термин «Value Score» в UI/данных НЕ встречается (англ. вариант «ценности»?): согласовано.
- вердикт/статус: нигде не смешаны в одном UI-файле.
- Value Score не используется; единый термин «ценность».
- даты в docs/index.html: ['11.09.2026']
- даты в docs/script.js: ['100, 1000']
- CHANGELOG-блоки: [('v2.0', '2026-09-11'), ('v1.3.1', '2026-09-10')]
- дисклеймер НА СТРАНИЦЕ docs/index.html: есть.
- ёлочки сбалансированы в docs/index.html («=3).
- ёлочки сбалансированы в docs/map.html («=0).
- ёлочки сбалансированы в docs/script.js («=0).
- латиницы в кириллическом тексте не найдено.
- опечатко-паттерны: серединные 2+пробела, баланс ёлочек, латиница в кириллице (выборочно)
- OK 200: https://clinicaltrials.gov/data-api/about-api (docs-api)
- OK 200: https://deadsno.github.io/brain-25-evidence/ (first-party)
- OK 200: https://deadsno.github.io/brain-25-evidence/map.html (first-party)
- OK 200: https://github.com/DeadSno/brain-25-evidence.git (external)
- OK 200: https://github.com/DeadSno/brain-25-evidence/issues/new/choose (external)
- OK 200: https://img.shields.io/badge/license-MIT-green (external)
- OK 200: https://img.shields.io/badge/supplements-41-orange (external)
- OK 200: https://img.shields.io/badge/tests-17%20passed-brightgreen (external)
- OK 200: https://img.shields.io/badge/version-v1.2-blue (external)
- OK 200: https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js (third-party-cdn)
- OK 200: https://deadsno.github.io/brain-25-evidence/ (first-party)
- OK 200: https://deadsno.github.io/brain-25-evidence/og.png (first-party)
- OK 200: https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap (third-party-cdn)
- OK 200: https://github.com/DeadSno/brain-25-evidence/issues/new?template=data-error.md (external)
- OK 200: https://mc.yandex.ru/metrika/tag.js?id=112465667 (third-party-cdn)
- OK 200: https://mc.yandex.ru/watch/112465667 (third-party-cdn)
- OK 200: https://deadsno.github.io/brain-25-evidence/ (first-party)
- ссылки проверены: 22 (HEAD→GET, UA, 2 ретрая; 429/бот-защита≠битые).

## Находки (≤25)
🔴 числа 41/81: устаревшее «41» в UI/описаниях: 4 шт  `docs/index.html:20: 41 добав; docs/index.html:20: — 41; docs/script.js:39: 41 добав; docs/script.js:39: — 41`
🔴 числа 41/81: README-бейдж supplements => 41 (а data.json=81)  `README.md:9`
🔴 числа 41/81: README-бейдж version => v1.2 (текущий v2.0)  `README.md:8`
🔴 числа 41/81: README-бейдж tests => 17 passed (сейчас 24+1 deselected)  `README.md:10`
🟡 числа 41/81: в README ещё 12 упоминаний «41» (данные-раздел/method), см. файл  `README.md:132-140`
🟡 даты: README-подвал: «v1.2, 09.09.2026» (версия/дата), может расходиться с v2.0  `README.md:295`
🔴 дисклеймер: на docs/map.html дисклеймера на странице нет  `docs/map.html`
🟡 дисклеймер: в модалках (script.js modalBody) дисклеймера/ссылки на него нет — только на странице  `docs/script.js:148-161`
🟡 опечатки: двойной пробел в середине строки: 2 вхождений  `docs/map.html:59; docs/script.js:29`
🟡 ссылки: не верифицировано (5): 429/бот-защита/CDN  `docs/index.html: https://fonts.googleapis.com → 404 (CDN не верифицировано); docs/index.html: https://fonts.gstatic.com → 404 (CDN не верифицировано); docs/script.js: https://t.me/share/url?url= → DNR:TimeoutError (бот-защита, не считается битой); docs/script.js: https://vk.com/share.php?url= → 418 (бот-защита, не считается битой)`
