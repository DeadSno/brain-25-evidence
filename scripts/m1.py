import pathlib
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')
frag = (
    "    (s.price != null\n"
    "      ? '<div class=\"price\">' + s.price + ' ₽/мес</div>' + priceSrcLink(s)\n"
    "      : '<div class=\"price noPrice\">цена не найдена · <a target=\"_blank\" rel=\"noopener\" href=\"' +\n"
    "        'https://github.com/DeadSno/brain-25-evidence/issues/new?title=' +\n"
    "        encodeURIComponent('Цена не найдена: ' + s.id) + '\">предложить</a></div>') +\n"
)
n = t.count(frag)
assert n == 1, 'найдено ' + str(n) + ' вхождений'
t = t.replace(frag, '', 1)
p.write_text(t, encoding='utf-8')
print('M1 готово. осталось "предложить":', t.count('предложить'))
