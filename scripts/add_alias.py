import pathlib, re
p = pathlib.Path('src/content.py')
t = p.read_text(encoding='utf-8')
old = "INTERACTIONS_ALIAS = {"
new = "INTERACTIONS_ALIAS = {\n    \"NMN/NR\": \"NMN\","
if old in t and '"NMN/NR": "NMN"' not in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding='utf-8')
    print('alias NMN/NR -> NMN добавлен')
else:
    print('alias уже есть или шаблон не найден')
