# Этап 5: canonical на корневых + RSS-фид

Ветка `v5.6-dev`. Работа в `C:\analytics\brain-25-evidence`. Коммит не делался.

## 1. Canonical: 11 файлов

A1 нашёл 13 корневых без canonical. Минус 2 исключения (A4) = **11 целевых
файлов**, ровно как ожидалось.

Формат на `index.html` (A2):

```html
<link rel="canonical" href="https://deadsno.github.io/brain-25-evidence/">
```

Добавлено тем же форматом, по одному файлу, все правки через Edit:

| Файл | canonical |
|---|---|
| atlas.html | `/atlas.html` |
| calculator.html | `/calculator.html` |
| faq.html | `/faq.html` |
| feedback.html | `/feedback.html` |
| glossary.html | `/glossary.html` |
| graph.html | `/graph.html` |
| interactions.html | `/interactions.html` |
| map.html | `/map.html` |
| methodology.html | `/methodology.html` |
| support.html | `/support.html` |
| trends.html | `/trends.html` |

Якорь — строка `<meta property="og:url" ...>`, уникальная в каждом файле.
Её URL совпадает с добавляемым canonical, так что тег не может разойтись с
og:url по недосмотру.

**Расхождение с заданием.** В 8 файлах og:url начинается с отступа, в 3
(`interactions`, `map`, `trends`) — с нуля. Первые три попытки Edit на
нетривиальном отступе не прошли; отступ выровнен по факту из файла, а не
угадан.

A5, резолв на живом сайте — 11/11 HTTP 200:

```
200 .../atlas.html       200 .../graph.html        200 .../support.html
200 .../calculator.html  200 .../interactions.html 200 .../trends.html
200 .../faq.html         200 .../map.html
200 .../feedback.html    200 .../methodology.html
200 .../glossary.html
```

Исключения не тронуты: canonical в `offline.html` и
`google4a9d23e35c6c3e23.html` — 0.

## 2. RSS: feed.xml

B1 подтвердил: в `docs/sup/kreatin.html` есть и JSON-LD, и og:image (2
совпадения). Дополнительно проверено в браузере на отрисованной странице —
`jsonLd: true`, `ogImage: true`.

Создан `scripts/build_feed.py` (генератор) и `docs/feed.xml`.

**Файл:** 86 237 байт, **131 запись** (130 карточек + каталог `sup/index.html`).

RSS 2.0, канал `brain-25-evidence`, описание «Доказательные данные о БАДах»,
`lang=ru`, `atom:link rel="self"` на сам фид.

Решения по содержимому:

- **Даты.** У карточек `pubDate` взят из поля `updated` в `docs/data.json` —
  единственного источника, который знает о правке данных (4 разные даты:
  2026-09-16 ×81, 09-23 ×26, 09-22 ×13, 09-25 ×10). Для каталога — дата
  последнего коммита файла, сам каталог генерируется `build_sup.py`, а не
  правится в data.json.
- **Время суток** = `00:00:00 UTC`: в data.json хранится только дата, а RSS 2.0
  требует полный RFC 822 timestamp. Выдумывать время правки, которого нет в
  источнике, нельзя.
- **Что НЕ в ленте.** Корневые разделы (`atlas`, `faq`, `graph`, ...) не
  включены: они меняются раз в месяц и только при перегенерации, а подписчик
  получает письмо на каждое изменение. Плюс `offline.html` и `google*.html` —
  служебные, те же исключения что и в `build_sitemap.py`.
- **Порядок** — по убыванию `updated`, затем по `code` (порядок карточек на
  сайте). Свежие правки наверху, порядок детерминирован.
- **guid** = URL с `isPermaLink="true"`, проверено: у всех 131 guid == link.
- **Источник слагов** — `slugify` импортирован из `build_sup.py`, а не
  продублирован. Проверено: 130 слагов, 130 уникальных, 0 отсутствующих
  файлов, 0 лишних файлов в `docs/sup/`.
- Отсутствие `updated` в записи — **ошибка сборки**, а не тихая подстановка
  даты запуска: иначе в ленте были бы записи «обновлено сегодня» для
  материала, который никто не трогал, и подписчик получал бы пустые письма.

B4, проверки:

| Проверка | Результат |
|---|---|
| `ET.parse('docs/feed.xml')` | OK, root `rss`, 131 item |
| Ссылки резолвятся локально | 131/131, битых 0 |
| Уникальность ссылок | 131 уникальный |
| `guid == link` | 131/131 |
| `pubDate` в RFC 822 | 131/131 |
| Пустые title/description/category | 0 |
| Управляющие символы в файле | нет |
| Идемпотентность (2 прогона) | sha256 `caa1c780e74183b5` оба раза |
| Через HTTP + DOMParser в браузере | 200, `text/xml`, parseError нет, 131 item |

## 3. `<link rel="alternate">`

Тег добавлен в 143 страницы:

- **12 корневых** — atlas, calculator, faq, feedback, glossary, graph,
  index, interactions, map, methodology, support, trends.
- **131 в `docs/sup/`** — через оба шаблона (`sup.html.j2` для 130 карточек,
  `sup_index.html.j2` для каталога), затем `build_sup.py` пересобрал раздел.

**Расхождение с заданием.** B3 просил «вручную в 13 корневых». В `docs/` 14
корневых html, минус 2 исключения A4 = **12**. 13 получить не из чего; 12 —
это полный набор контентных страниц, все 12 проверены.

Исключения (`offline.html`, `google*.html`) тег не получили намеренно.

Проверка в браузере на живых страницах: `index.html` и `sup/kreatin.html` —
alternate резолвится, `type`, `title`, `href` на месте, 0 ошибок в консоли.

**Побочная находка.** Первый вариант шаблона оставлял в выводе строку из
одних пробелов — Jinja-комментарий печатался, а перевод строки после него
попадал в результат. Заметно на размере: 1 758 771 → 1 758 261 байт (−510,
ровно 131 × 4 пробела + переводы строк). Исправлено: комментарий закрыт без
перевода строки, как уже сделано у `style.css` в этом же шаблоне. Итоговый
diff по всем 131 страницам — **+1 строка, 0 удалений**.

## 4. CI check

В `.github/workflows/tests.yml` добавлено:

```yaml
- name: Sitemap check
  run: python scripts/build_sitemap.py --check

- name: Feed check
  run: python scripts/build_feed.py --check
```

`Feed check` добавлен сверх задания по той же причине, что и сам фид: он
собирается из содержимого `docs/`, значит тоже имеет право разойтись с ним.

**Найденная проблема, без которой CI падал бы на пустом месте.**
`actions/checkout@v4` по умолчанию даёт `fetch-depth: 1`. При такой истории
`git log -1 -- docs/<файл>` у **любого** файла возвращает дату HEAD, а
генератор берёт `lastmod` из даты правки самого файла. В `docs/sitemap.xml` все
143 записи несут `2026-10-06`, дата HEAD — `2026-10-07`.

Воспроизведено клоном `--depth 1`: `--check` падает, расхождение ложное.
С полной историей (690 коммитов) — проходит. Поэтому в шаг checkout добавлен
`fetch-depth: 0` с комментарием, объясняющим, почему он обязателен; иначе
перв же прогон CI был бы красным без реальной причины.

Проверки:

| Проверка | Результат |
|---|---|
| `build_sitemap.py --check` локально | exit 0, 143 URL |
| `build_feed.py --check` локально | exit 0, 131 записей |
| YAML парсится (pyyaml) | OK, 7 шагов в `pytest` |
| `fetch-depth: 0` на месте | `{'fetch-depth': 0}` |
| Симуляция CI: полный клон + рабочее состояние | sitemap 0, feed 0, feed.xml парсится |
| Симуляция CI: клон `--depth 1` (старый вариант) | **FAIL**, exit 1 — ложное расхождение |

## 5. Регрессии

`pytest -q`: **790 passed, 2 skipped**, 1 warning (известный, про
`KNOWN_DEAD_CSS`, не связан). Пропуски — snapshot-эталоны, они не гоняются
без `RUN_SNAPSHOTS=1`.

`docs/sitemap.xml` в `git status` был изменён **до** начала работы (этап 4) и
в этой сессии не трогался: `--check` файл не пишет, генератор без флага не
запускался.

## 6. `git diff --stat`

По затронутым в этом этапе путям:

```
 .github/workflows/tests.yml          | 21 +++++++++++++++++++++
 docs/atlas.html                      |  2 ++
 docs/calculator.html                 |  2 ++
 docs/faq.html                        |  2 ++
 docs/feedback.html                   |  2 ++
 docs/glossary.html                   |  2 ++
 docs/graph.html                      |  2 ++
 docs/index.html                      |  1 +
 docs/interactions.html               |  2 ++
 docs/map.html                        |  2 ++
 docs/methodology.html                |  2 ++
 docs/support.html                    |  2 ++
 docs/trends.html                     |  2 ++
 docs/sup/*.html  (130 файлов)        |  1 +  каждый
 docs/sup/index.html                  |  1 +
 templates/sup.html.j2                |  6 ++++++
 templates/sup_index.html.j2          |  4 ++++
 146 files changed, 185 insertions(+)
```

Ни одного удаления во всём диффе. Новые файлы (untracked):

```
 docs/feed.xml            86 237 байт, 131 запись
 scripts/build_feed.py    генератор, --check для CI
```

`scripts/build_sitemap.py` тоже untracked — он от предыдущего этапа.

## Стоп-условия

Не сработали ни одно:

- canonical URL не резолвится → все 11 отдали 200;
- RSS XML невалиден → `ET.parse` OK, DOMParser в браузере OK;
- CI check падает → локально и в симуляции CI оба exit 0.

## Что осталось за рамками

- `feed.xml` не добавлен в `sitemap.xml` — он не HTML-страница, и текущий
  генератор sitemap собирает только `.html`. Проверка через
  `robots.txt`/дымпу не делалась.
- `sw.js` кеширующий список не обновлён: `feed.xml` на клиенте не появится,
  пока офлайн-слой его не узнает. Отдельная задача.
- `data.json`-даты покрывают только карточки; у корневых страниц RSS-дат нет
  вовсе — они в ленту и не попадают.
