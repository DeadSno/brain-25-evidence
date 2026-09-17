import json
d = json.load(open('docs/data.json', encoding='utf-8'))
n = len(d)
print('всего добавок:', n)
def filled(v):
    if v is None: return False
    if isinstance(v, (list, dict, str)): return len(v) > 0
    return True
keys = []
for s in d:
    for k in s.keys():
        if k not in keys: keys.append(k)
print(f'{"поле":26} {"заполн.":>8} {"%":>5}')
for k in keys:
    c = sum(1 for s in d if filled(s.get(k)))
    print(f'{k:26} {c:>8} {100*c//n:>4}%')
print()
for k in ['reviews','wiki','wiki_views','trends','ongoing','citations','ma_citations','hedges_g','dosage','course','onset','caution','interactions','myths','food_sources','guidelines','how_to_choose']:
    miss = [s['id'] for s in d if not filled(s.get(k))]
    if miss:
        print(f'{k}: пусто у {len(miss)} -> {miss[:10]}')
