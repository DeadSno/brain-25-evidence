import pathlib
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')
# Заменяем PROF_LABELS с 5 на 4
old = "const PROF_LABELS = ['Наука', 'База МА', 'Спрос', 'Интерес', 'Доступность'];"
new = "const PROF_LABELS = ['Наука', 'База МА', 'Спрос', 'Интерес'];"
t = t.replace(old, new)
p.write_text(t, encoding='utf-8')
print('обновлён script.js: убрана ось "Доступность" из радар-меток')
