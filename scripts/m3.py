import pathlib, re

# --- index.html: удалить 4 HTML-элемента ---
h = pathlib.Path('docs/index.html')
html = h.read_text(encoding='utf-8')

html = re.sub(r'\s*<option value="price_asc">Сначала дешёвые</option>', '', html)
html = re.sub(r'\s*<button id="tabPrice"[^>]*>Цена vs наука</button>', '', html)
html = re.sub(r'\s*<button id="axisPrice"[^>]*>Цена ₽/мес</button>', '', html)
html = re.sub(r'\s*<button class="preset" data-preset="cheap"[^>]*>💰 До 500[^\n]*</button>', '', html)

h.write_text(html, encoding='utf-8')
print('index.html: 4 элемента цены удалены')

# --- script.js: удалить обработчики и упоминания ---
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')

# Обработчики кликов
t = re.sub(r"\$\('tabPrice'\)\.onclick\s*=\s*\(\)\s*=>\s*setChartTab\('price'\);\s*\n", '', t)
t = re.sub(r"\$\('axisPrice'\)\.onclick\s*=\s*\(\)\s*=>\s*setAxisX\('price'\);\s*\n", '', t)

# Ветка пресета 'cheap'
t = re.sub(r"\s*else if \(p === 'cheap'\) \{ presetCheap = !presetCheap; on = presetCheap; \}", '', t)

# Фильтр presetCheap в applyFilters
t = re.sub(r"\s*if \(presetCheap &&.*?return false;\n", '', t)

# Сортировка price_asc
t = re.sub(r"\s*price_asc: \(a, b\) => \(a\.price \|\| 1e9\) - \(b\.price \|\| 1e9\),", '', t)

# Переменная presetCheap
t = re.sub(r"let presetCheap = false, presetOngoing = false;\s*", "let presetOngoing = false;\n", t)

p.write_text(t, encoding='utf-8')
print('script.js: обработчики кнопок цены удалены')
