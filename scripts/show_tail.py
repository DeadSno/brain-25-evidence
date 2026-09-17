import pathlib
t = pathlib.Path('docs/index.html').read_text(encoding='utf-8')
i = t.find('<section id="qaSection"')
print('=== ОТ qaSection ДО КОНЦА ===')
print(t[i:])
print('=== КОНЕЦ ===')
