import json, pathlib
from collections import Counter
p = pathlib.Path('docs/data.json')
d = json.loads(p.read_text(encoding='utf-8'))

verdict_to_code = {
    'работает': 1,
    'зависит от контекста': 0,
    'не подтверждено': -1
}

fixed = 0
for s in d:
    v = s.get('verdict', '')
    if v in verdict_to_code:
        if s.get('code') != verdict_to_code[v]:
            s['code'] = verdict_to_code[v]
            fixed += 1

p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
print('перезаписано code:', fixed)
print('распределение code:', dict(Counter(s.get('code') for s in d)))
