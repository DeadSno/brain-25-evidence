import pathlib, re
t = pathlib.Path('docs/script.js').read_text(encoding='utf-8')
for pat in [r"💰 <b>' \+ \(s\.price", r"priceSrcLink\(s\)", r"ppe\(s\)", r"historyPriceBlock\(s\)"]:
    m = re.search(pat, t)
    if m:
        print(f'=== {pat} ===')
        print(repr(t[max(0,m.start()-80):m.end()+220]))
        print()
