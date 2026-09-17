import pathlib
t = pathlib.Path('docs/index.html').read_text(encoding='utf-8')
print(f'всего символов: {len(t)}')
print(f'строк: {t.count(chr(10))}')
print()
# найдём все section/footer
for marker in ['qaSection', 'qaGrid', '</section>', '</footer>', '<footer', 'modalOverlay']:
    idx = t.find(marker)
    if idx >= 0:
        # покажем контекст
        start = max(0, idx-30)
        end = min(len(t), idx+len(marker)+100)
        print(f'--- {marker} на позиции {idx} ---')
        print(repr(t[start:end]))
        print()
