import pathlib, re

# --- index.html: убрать кнопку-вкладку квадранта + переименовать заголовок ---
h = pathlib.Path('docs/index.html')
html = h.read_text(encoding='utf-8')
html = re.sub(r'\s*<button id="tabQuadrant"[^>]*>Квадрант доказательности</button>', '', html)
html = html.replace('Цена vs Доказательность', 'Доказательность: индекс науки vs объём исследований')
html = html.replace('«индекс науки» и «₽ за единицу эффекта»', '«индекс науки»')
h.write_text(html, encoding='utf-8')
print('index.html: вкладка квадранта убрана, заголовок переименован')

# --- script.js: убрать обработчики квадранта, вернуть пузырь дефолтом ---
p = pathlib.Path('docs/script.js')
lines = p.read_text(encoding='utf-8').split('\n')
out, killed = [], []
for ln in lines:
    s = ln.strip()
    if s.startswith("$('tabQuadrant').onclick"):
        killed.append('tabQuadrant.onclick'); continue
    if s.startswith("$('tabQuadrant').classList.toggle"):
        killed.append('tabQuadrant.classList'); continue
    out.append(ln)
t = '\n'.join(out)
t = t.replace("let chartTab = 'quadrant';", "let chartTab = 'price';")
p.write_text(t, encoding='utf-8')
print('убито:', killed)
print('tabQuadrant осталось:', t.count('tabQuadrant'))
