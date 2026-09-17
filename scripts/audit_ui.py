import pathlib, re

# Размер скриптов
print('=== Размеры файлов (KB) ===')
for f in ['docs/script.js', 'docs/science2.js', 'docs/style.css', 'docs/index.html']:
    p = pathlib.Path(f)
    kb = round(p.stat().st_size / 1024, 1)
    print(f'  {f}: {kb} KB')

# A11y: aria-labels, roles
print('\n=== A11y: aria-label / role в index.html ===')
idx = pathlib.Path('docs/index.html').read_text(encoding='utf-8')
aria = re.findall(r'aria-[a-z]+', idx)
roles = re.findall(r'role="[^"]*"', idx)
print(f'  aria-* атрибутов: {len(aria)} ({set(aria)})')
print(f'  role="...": {len(roles)}')

# alt у картинок
print('\n=== Картинки ===')
imgs = re.findall(r'<img[^>]*>', idx)
for img in imgs[:5]:
    print(f'  {img[:100]}')

# h1-h6 иерархия
print('\n=== Заголовки ===')
for lvl in range(1, 7):
    count = idx.count(f'<h{lvl}')
    if count: print(f'  h{lvl}: {count}')

# Скрипты в <head> vs в конце body
print('\n=== Скрипты ===')
for m in re.finditer(r'<script[^>]*src="([^"]+)"[^>]*>', idx):
    tag = m.group(0)
    src = m.group(1)
    defer = 'defer' in tag
    async_ = 'async' in tag
    print(f'  {src}: defer={defer}, async={async_}')
