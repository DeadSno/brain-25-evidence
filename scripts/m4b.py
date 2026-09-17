import pathlib

p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')

# 1. Шапка модалки: убрать «💰 — ·» (оставить только науку и MA)
old = " + ' · ' + '💰 <b>' + (s.price ? s.price + ' ₽/мес' : '—') + '</b>' + priceSrcLink(s)"
t = t.replace(old, '')

# 2. Вызов historyPriceBlock(s) в модалке
t = t.replace(" +\n    historyPriceBlock(s) +", '')

# 3. Удалить функции-заглушки (точные блоки)
funcs = [
    "function priceSrcLink(s) {\n  return '';\n}\n",
    "function ppe(s) {\n  return null;\n}\n",
    "function ppeReason(s) {\n  return 'Эффект ждёт верификации — ₽ за единицу эффекта не считаем';\n}\n",
    "function ppeModalLine(s) {\n  const v = ppe(s);\n  if (v == null) return '';\n  return '<div class=\"mrow\">📐 ' + ppeReason(s) + '</div>';\n}\n",
    "function historyPriceBlock(s) {\n  return '<div class=\"blockTitle\">💰 История цены</div>' +\n    '<div class=\"sparkline\">📈 Цена: динамика 90 дней</div>';\n}\n"
]
for f in funcs:
    t = t.replace(f, '')

# 4. Чарт: убрать строку про «💰 N добавок без цены»
old_chart = "? '💰 ' + nullPrice.length + ' добавок без цены — серые точки в зоне справа'"
t = t.replace(old_chart, "? ''")

# 5. Сравнение: убрать строку «₽ за единицу эффекта»
t = t.replace("['₽ за единицу эффекта', ppe(a) != null ? ppe(a) : ppeReason(a), ppe(b) != null ? ppe(b) : ppeReason(b)],\n", '')

p.write_text(t, encoding='utf-8')
print('💰 осталось:', t.count('💰'))
print('priceSrcLink осталось:', t.count('priceSrcLink'))
print('ppe осталось:', t.count('ppe('))
print('historyPriceBlock осталось:', t.count('historyPriceBlock'))
