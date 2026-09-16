import pathlib, re
p = pathlib.Path('docs/script.js')
js = p.read_text(encoding='utf-8')
pattern = r"const DOT_COLOR = \{[^}]*\};"
new = "const DOT_COLOR = { A: '#22c55e', B: '#84cc16', C: '#f59e0b', D: '#ef4444' };"
js2, n = re.subn(pattern, new, js)
if n == 0:
    print('НЕ НАЙДЕНО DOT_COLOR — ищем вручную')
    print('Текущая строка:')
    for line in js.splitlines():
        if 'DOT_COLOR' in line:
            print(' ', line)
else:
    p.write_text(js2, encoding='utf-8')
    print(f'заменено DOT_COLOR: {n} вхождение')
