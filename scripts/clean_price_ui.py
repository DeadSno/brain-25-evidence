import pathlib, re

p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')
changes = []

# 1. Удалить блок { key: 'price', ... } из CARDBLOCKS
old_price_block = r",\s*\{ key: 'price',\s*title: 'Сколько стоит и откуда цена'.*?\}\s*\];"
new_block = '];'
if re.search(old_price_block, t, re.DOTALL):
    t = re.sub(old_price_block, new_block, t, flags=re.DOTALL)
    changes.append('удалён блок price из CARDBLOCKS')

# 2. Заглушить priceSrcLink
t = re.sub(
    r"function priceSrcLink\(s\) \{[^}]+\}",
    "function priceSrcLink(s) { return ''; }",
    t
)
changes.append('заглушена priceSrcLink()')

# 3. Заглушить ppe, ppeReason, priceTip, ppeModalLine
for fn in ['ppe', 'ppeReason', 'priceTip', 'ppeModalLine']:
    t = re.sub(
        rf"function {fn}\([^)]*\) \{{[^}}]*\}}",
        f"function {fn}(s) {{ return ''; }}",
        t
    )
    changes.append(f'заглушена {fn}()')

# 4. Заглушить historyPriceBlock
t = re.sub(
    r"function historyPriceBlock\(s\) \{[^}]*\}",
    "function historyPriceBlock(s) { return ''; }",
    t
)
changes.append('заглушена historyPriceBlock()')

# 5. Убрать фильтр presetCheap (строка ~312)
t = re.sub(
    r"if \(presetCheap &&.*?return false;\n\s*",
    "",
    t
)
changes.append('удалён фильтр presetCheap')

# 6. Удалить сортировку price_asc
t = re.sub(
    r"price_asc: \(a, b\) => \(a\.price \|\| 1e9\) - \(b\.price \|\| 1e9\),\s*",
    "",
    t
)
changes.append('удалена сортировка price_asc')

# 7. Обновить pageTitle (убрать "цена vs")
t = t.replace(
    "БАДы: цена vs наука — 81 добавка через мета-анализы",
    "БАДы: что работает, а что нет — 81 добавка через мета-анализы"
)
changes.append('обновлён pageTitle (убрана "цена vs")')

# 8. Поменять дефолтный chartTab на quadrant
t = t.replace("let chartTab = 'price';", "let chartTab = 'quadrant';")
changes.append('дефолтный chartTab = quadrant')

# 9. presetCheap = false (без переключателя всё равно будет false, но обнулим явно)
#    (переменная остаётся, чтобы не сломать switch в строке 162)

p.write_text(t, encoding='utf-8')
print('script.js почищен:')
for c in changes:
    print(f'  ✓ {c}')
