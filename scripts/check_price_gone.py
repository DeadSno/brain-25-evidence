import json
d = json.load(open('docs/data.json', encoding='utf-8'))
price_fields = set()
for s in d:
    for k in s.keys():
        if 'price' in k.lower() or 'year_last' in k.lower():
            price_fields.add(k)
if price_fields:
    print('ОСТАЛИСЬ:', price_fields)
else:
    print('✓ Все поля цен удалены')
print()
print('Пример полей Креатина:')
s = next(x for x in d if x['id'] == 'Креатин')
for k in sorted(s.keys()):
    print(f'  {k}')
