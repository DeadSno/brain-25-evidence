import pathlib, re
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')
# Заглушки: удалить ЛЮБЫЕ function name(){return ''} и function name(){return null}
t = re.sub(r"function priceSrcLink\(s\)\s*\{[^}]*\}\s*\n?", '', t)
t = re.sub(r"function ppe\(s\)\s*\{[^}]*\}\s*\n?", '', t)
t = re.sub(r"function ppeReason\(s\)\s*\{[^}]*\}\s*\n?", '', t)
t = re.sub(r"function ppeModalLine\(s\)\s*\{[^}]*\}\s*\n?", '', t)
t = re.sub(r"function historyPriceBlock\(s\)\s*\{[\s\S]*?\}\s*\n?", '', t)
# Шапка модалки: удалить 💰-блок в строке с scienceIndex
t = re.sub(r"\s*['\"]?\s*\+\s*'·'\s*\+\s*'💰[^\n]{0,200}priceSrcLink\(s\)", '', t)
# Вызов historyPriceBlock(s)
t = t.replace('historyPriceBlock(s) +', '')
t = t.replace('historyPriceBlock(s)', '')
# ppeModalLine(s) в модалке
t = t.replace('ppeModalLine(s) +', '')
t = t.replace('+ ppeModalLine(s)', '')
# Сравнение: строка с ₽ за единицу эффекта
t = re.sub(r"\['₽ за единицу эффекта'[^\]]*\],\s*\n", '', t)
# Чарт: «💰 N добавок без цены»
t = re.sub(r"\?\s*'💰 '[^\n]*", "? ''", t)
p.write_text(t, encoding='utf-8')
print('💰:', t.count('💰'), '| priceSrcLink:', t.count('priceSrcLink'))
print('ppe:', t.count('ppe('), '| historyPriceBlock:', t.count('historyPriceBlock'))
