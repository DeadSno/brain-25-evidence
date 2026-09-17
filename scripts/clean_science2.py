import pathlib, re

p = pathlib.Path('docs/science2.js')
t = p.read_text(encoding='utf-8')

# Удалить блок C4 (спарклайн цены) — между комментарием C4 и закрывающей });
# Ищем от "C4: спарклайн" до конца IIFE
pattern = r"// ========== C4:.*?^\}\)\(\);?\s*$"
# Более надёжный способ — удалить от "C4:" до "MutationObserver" или конца
# Найдём точные позиции
c4_start = t.find('// ========== C4:')
if c4_start == -1:
    print('Блок C4 не найден')
else:
    # Ищем конец — MutationObserver блок идёт после C4
    mo_marker = '// ========== M:'
    if mo_marker in t:
        mo_start = t.find(mo_marker)
        # Удаляем всё от C4 до MutationObserver
        t = t[:c4_start] + t[mo_start:]
        p.write_text(t, encoding='utf-8')
        print('✓ Удалён блок спарклайна цены (C4) из science2.js')
    else:
        # Удаляем до конца IIFE
        iife_end = t.rfind('})();')
        if iife_end > c4_start:
            t = t[:c4_start] + t[iife_end:]
            p.write_text(t, encoding='utf-8')
            print('✓ Удалён блок C4 (до конца IIFE) из science2.js')
