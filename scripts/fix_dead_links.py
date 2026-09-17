import pathlib, re
for f in ['docs/index.html', 'docs/map.html']:
    p = pathlib.Path(f)
    h = p.read_text(encoding='utf-8')
    # удаляем всю строку <p>...</p> со ссылкой на for_doctors
    h2, n = re.subn(r'<p[^>]*>.*?for_doctors\.html.*?</p>', '', h, flags=re.DOTALL)
    p.write_text(h2, encoding='utf-8')
    print(f'{f}: удалено {n} строк')
