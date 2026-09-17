import json
from collections import Counter

d = json.load(open('docs/data.json', encoding='utf-8'))
total = len(d)
with_grade = sum(1 for s in d if s.get('grade'))
print('всего добавок:', total)
print('с грейдами:', with_grade, '/', total)
print()
print('распределение грейдов:')
grades = Counter(s.get('grade', 'без грейда') for s in d)
for g in ['A', 'B', 'C', 'D', 'без грейда']:
    print(' ', g + ':', grades.get(g, 0))
print()
print('примеры:')
for s in d[:5]:
    if s.get('grade'):
        name = s['name']
        grade = s.get('grade')
        verdict = s.get('verdict')
        print(' ', name, '->', 'grade=' + grade, 'verdict=' + str(verdict))

missing = [s['name'] for s in d if not s.get('grade')]
if missing:
    print()
    print('БЕЗ ГРЕЙДА:', missing)
