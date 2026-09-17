import pathlib
p = pathlib.Path('docs/script.js')
lines = p.read_text(encoding='utf-8').split('\n')
out, killed = [], []
for ln in lines:
    s = ln.strip()
    if s.startswith("$('tabPrice').classList.toggle"):
        killed.append('tabPrice.classList'); continue
    if s.startswith("else if (p === 'cheap')"):
        killed.append('preset cheap branch'); continue
    if s.startswith('if (presetCheap &&'):
        killed.append('presetCheap filter'); continue
    if s.startswith('price_asc:'):
        killed.append('price_asc sorter'); continue
    if s.startswith("if (axisX === 'price') return"):
        killed.append('axisVal price branch'); continue
    out.append(ln)
t = '\n'.join(out)
t = t.replace("let presetCheap = false, presetOngoing = false;", "let presetOngoing = false;")
t = t.replace("let chartTab = 'price';", "let chartTab = 'quadrant';")
t = t.replace("let axisX = 'price';", "let axisX = 'ma';")
t = t.replace("price: 'axisPrice', ", "")
t = t.replace("price: 'Цена за месяц (₽)', ", "")
t = t.replace("['price', 'ma', 'rct', 'year'].forEach", "['ma', 'rct', 'year'].forEach")
p.write_text(t, encoding='utf-8')
print('убито строк:', killed)
print('осталось tabPrice/axisPrice/presetCheap:',
      t.count('tabPrice'), t.count('axisPrice'), t.count('presetCheap'))
