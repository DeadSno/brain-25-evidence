import json, pathlib
p = pathlib.Path('docs/data.json')
d = json.loads(p.read_text(encoding='utf-8'))

removed = 0
for s in d:
    for k in ['price', 'price_source', 'price_date', 'year_last_ma', 'price_month']:
        if k in s:
            del s[k]
            removed += 1

p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'удалено {removed} полей у {len(d)} добавок')
