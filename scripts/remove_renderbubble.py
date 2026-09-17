import pathlib, re

p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')

# 1. Найти и удалить функцию renderBubble целиком
# Ищем "function renderBubble" и идём до её закрывающей }
start = t.find('function renderBubble(data) {')
if start != -1:
    # Считаем скобки чтобы найти конец функции
    brace_count = 0
    in_func = False
    end = start
    for i, ch in enumerate(t[start:], start):
        if ch == '{':
            brace_count += 1
            in_func = True
        elif ch == '}':
            brace_count -= 1
            if in_func and brace_count == 0:
                end = i + 1
                break
    # Удаляем функцию + пустые строки после неё
    while end < len(t) and t[end] in ' \t\n\r':
        end += 1
    t = t[:start] + t[end:]
    print(f'✓ Удалена функция renderBubble (с {start} по {end})')
else:
    print('⚠ Функция renderBubble не найдена')

# 2. Обновить комментарий строки ~391
t = t.replace(
    '// ===== v2.6: сменная ось X графика (Цена/MА/РКИ/Год) =====',
    '// ===== v2.6: сменная ось X графика (МА/РКИ/Год) ====='
)
print('✓ Обновлён комментарий: убрана "Цена"')

p.write_text(t, encoding='utf-8')
