# CONVENTIONS — brain-25-evidence

## Граф — генерируется

Артефакты графа собираются скриптами, править их вручную запрещено.

- `docs/graph_data.json` = `scripts/build_graph_data.py`
  (входы: `docs/data.json` + `docs/effect_tags.json` +
  `docs/graph_mech_edges.json` — 255 curated мех-рёбер)
- `docs/graph_positions.json` = `scripts/build_graph_positions.py`
  (вход: `docs/graph_data.json`, детерминированная круговая раскладка)

Флаги:
- `python scripts/build_graph_data.py --check` — сверка без записи,
  exit 1 при расхождении.
- `python scripts/build_graph_positions.py --check` — то же для позиций.

`--check` обоих генераторов встроен в `.githooks/pre-commit` и
блокирует коммит при рассинхроне артефакта с исходными данными.

Структура `graph_data.json` не меняется (совместимость с
`graph.html` / `interactions.html`). Поле `group` не добавляется
(структура B — батч 2).

История ручного файла: `docs/graph_data.json` собирался вручную до
коммита `8b16d15` (канонизация), затем заменён выходом
`build_graph_data.py`.

## Страницы-редиректы

Все старые ссылки на `graph.html` и `atlas.html` ведут через JS-редиректы.
Файлы оставлены (закладки и внешние ссылки не получают 404), но каждая —
заглушка из трёх частей: `<meta http-equiv="refresh" content="0; url=…">`,
`<link rel="canonical" href="…/interactions.html">` и
`window.location.replace(…)` в `<script>`.

- `docs/graph.html` → `interactions.html#graph`
- `docs/atlas.html` → `interactions.html#mech`

Канонический URL один — `interactions.html`. Обе заглушки помечены
`<meta name="robots" content="noindex, follow">` и выведены из
`docs/sitemap.xml` (генератор — `scripts/build_sitemap.py`). Новые ссылки на
`graph.html` / `atlas.html` не добавлять, в навбар не возвращать: это
совместимость со старыми адресами, а не точки входа.
