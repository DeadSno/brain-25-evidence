import pathlib
p = pathlib.Path('docs/style.css')
lines = p.read_text(encoding='utf-8').splitlines()

dead_markers = ['vworks', 'vcontext', 'vunproven']
clean = []
seen_flat_block = 0
skip = 0
for i, line in enumerate(lines):
    if any(m in line for m in dead_markers):
        continue
    if skip > 0:
        skip -= 1
        continue
    if line.strip().startswith('.verdict.v1  { background: #22c55e !important; }'):
        seen_flat_block += 1
        if seen_flat_block > 1:
            skip = 2
            continue
    clean.append(line)

p.write_text('\n'.join(clean) + '\n', encoding='utf-8')
print('строк было:', len(lines), '-> стало:', len(clean))
