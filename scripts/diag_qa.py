import json, pathlib
d = json.loads(pathlib.Path('docs/data.json').read_text(encoding='utf-8'))
print('id с NMN:')
for s in d:
    if 'NMN' in s['id']:
        print(' ', repr(s['id']))

t = pathlib.Path('docs/index.html').read_text(encoding='utf-8')
i = t.find('qaSection')
if i == -1:
    print('qaSection НЕ найден')
else:
    end = t.find('</section>', i)
    print()
    print('=== qaSection ===')
    print(t[i-60:end+12])
