import json
d = json.load(open('docs/data.json', encoding='utf-8'))
s = d[0]
print('Добавка:', s.get('name'))
print()
print('Все поля:')
for k, v in s.items():
    print(f'  {k}: {repr(v)[:80]}')
