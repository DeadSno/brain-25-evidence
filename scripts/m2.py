import pathlib, re

# --- script.js: убрать блок price из CARDBLOCKS (2 строки, последний элемент) ---
p = pathlib.Path('docs/script.js')
lines = p.read_text(encoding='utf-8').split('\n')
idx = [k for k, l in enumerate(lines) if "{ key: 'price'," in l]
assert len(idx) == 1, f'ожидал 1 блок price, нашёл {len(idx)}'
i = idx[0]
assert 'priceSrcLink(s)' in lines[i+1], 'вторая строка блока не совпала'
prev = lines[i-1]
assert prev.rstrip().endswith('},'), 'предыдущая строка не заканчивается на },'
lines[i-1] = prev.rstrip()[:-1]
del lines[i:i+2]
p.write_text('\n'.join(lines), encoding='utf-8')
print('script.js: блок price удалён из CARDBLOCKS')

# --- tests/test_education.py: убрать "price" из BLOCK_KEYS, 15 -> 14 ---
q = pathlib.Path('tests/test_education.py')
t = q.read_text(encoding='utf-8')
t2 = re.sub(r',\s*"price"\]', ']', t, count=1)
assert t2 != t, 'BLOCK_KEYS: "price" не найден'
t = t2
assert '== 15' in t or '15 блоков' in t, 'нет упоминания 15'
t = t.replace('== 15', '== 14').replace('15 блоков', '14 блоков')
q.write_text(t, encoding='utf-8')
print('test_education: 15 -> 14')
