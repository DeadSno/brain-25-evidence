import pathlib

p = pathlib.Path('docs/index.html')
t = p.read_text(encoding='utf-8')
old = '<option value="price_asc">Сначала дешёвые</option>\n'
if old in t:
    t = t.replace(old, '')
    p.write_text(t, encoding='utf-8')
    print('✓ Удалён option "Сначала дешёвые" из index.html')
else:
    # Попробуем с другим форматированием
    t2 = t.replace('<option value="price_asc">Сначала дешёвые</option>', '')
    if t2 != t:
        p.write_text(t2, encoding='utf-8')
        print('✓ Удалён option "Сначала дешёвые" из index.html (вариант 2)')
    else:
        print('option price_asc не найден — уже удалён')
