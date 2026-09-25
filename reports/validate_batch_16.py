# -*- coding: utf-8 -*-
import io, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('reports/q14_batch_16_proposal.json', encoding='utf-8'))

LIMITS = {
    'about': (30, 160), 'who_needs': (40, 180), 'onset': (30, 150),
    'myths': (60, 220), 'food_sources': (25, 180), 'guidelines': (40, 180),
    'how_to_choose': (35, 180),
}
GRADES = {'A', 'B', 'C', 'D'}
VERDICTS = {'работает', 'зависит от контекста', 'не подтверждено'}
STRENGTH = {'сильно', 'умеренно', 'слабо', 'контекст', 'маркетинг'}

errors = []
for name, c in d.items():
    for f, (lo, hi) in LIMITS.items():
        n = len(c.get(f, ''))
        if not (lo <= n <= hi):
            errors.append(f'{name}.{f}={n} вне [{lo},{hi}]')
    if c.get('verdict') not in VERDICTS:
        errors.append(f'{name}: verdict={c.get("verdict")}')
    if c.get('grade') not in GRADES:
        errors.append(f'{name}: grade={c.get("grade")}')
    if not (2 <= len(c.get('mechs', [])) <= 4):
        errors.append(f'{name}: mechs={len(c.get("mechs", []))}')
    for m in c.get('mechs', []):
        if len(m) != 3 or m[2] not in STRENGTH:
            errors.append(f'{name}: mech bad {m}')
    for e in c.get('effects', []):
        if not (5 <= len(e) <= 40):
            errors.append(f'{name}: effect len {len(e)} "{e}"')
    for ks in c.get('key_sources', []):
        if not isinstance(ks.get('year'), int):
            errors.append(f'{name}: year not int {ks.get("year")}')
        if not ks.get('journal'):
            errors.append(f'{name}: journal missing {ks.get("pmid")}')
        if not ks.get('title'):
            errors.append(f'{name}: title missing')
    for it in c.get('interactions', []):
        if 'with' not in it:
            errors.append(f'{name}: interactions без with')
    for f in ['about', 'who_needs', 'onset', 'myths', 'food_sources', 'guidelines',
              'how_to_choose', 'dosage', 'course', 'caution', 'upper_limit']:
        if not c.get(f):
            errors.append(f'{name}: поле {f} пустое')
    for f in ['mechs', 'effects', 'interactions', 'key_sources']:
        if not isinstance(c.get(f), list):
            errors.append(f'{name}: {f} не список')

print('Карточек:', len(d), '| Ошибок:', len(errors))
for e in errors:
    print('  -', e)
if not errors:
    for name, c in d.items():
        print(f"{name}: {c['grade']} {c['verdict']} mechs={len(c['mechs'])} "
              f"effects={c['effects']} "
              f"src={[s['pmid'] for s in c['key_sources']]}")
