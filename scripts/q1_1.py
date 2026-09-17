import pathlib, re

# === script.js: убрать дисклеймер из модалки ===
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')
# Строка 345: '<div class="mrow" style="font-size:.85rem;opacity:.9">⚠️ Проект не является...'
t = re.sub(r"\s*'<div class=\"mrow\" style=\"font-size:\.85rem;opacity:\.9\">[^<]*⚠️ Проект не является медицинской рекомендацией[^<]*</div>' \+\s*\n", '', t)
p.write_text(t, encoding='utf-8')
print('✓ script.js: дисклеймер из модалки убран')

# === index.html: убрать ссылку на for_doctors ===
h = pathlib.Path('docs/index.html')
html = h.read_text(encoding='utf-8')
html = re.sub(r'\s*<a href="for_doctors\.html">[^<]*</a>\s*·', '', html)
h.write_text(html, encoding='utf-8')
print('✓ index.html: ссылка "Для врачей" убрана')

# === map.html: убрать ссылку на for_doctors ===
m = pathlib.Path('docs/map.html')
mhtml = m.read_text(encoding='utf-8')
mhtml = re.sub(r'\s*<a href="for_doctors\.html">[^<]*</a>\s*·', '', mhtml)
m.write_text(mhtml, encoding='utf-8')
print('✓ map.html: ссылка "Для врачей" убрана')
