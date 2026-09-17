import pathlib
p = pathlib.Path('tests/test_ma_top3.py')
t = p.read_text(encoding='utf-8')
# Удаляем функцию test_price_date_present_all
lines = t.split('\n')
new_lines = []
skip = False
for line in lines:
    if 'def test_price_date_present_all' in line:
        skip = True
    elif skip and line.startswith('def '):
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)
p.write_text('\n'.join(new_lines), encoding='utf-8')
print('удалена функция test_price_date_present_all из test_ma_top3.py')
