import json, pathlib, re
from pathlib import Path

AUDIT_DIR = Path('data/processed/audit')
DATA_JSON = Path('docs/data.json')

def extract_json_from_md(md_text):
    # Извлекает JSON-блок между { и }
    m = re.search(r'\{[^{}]*"id"[^{}]*"updated"[^{}]*\}', md_text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except:
        return None

# Загружаем data.json
data = json.loads(DATA_JSON.read_text(encoding='utf-8'))

# Строим словарь аудита по имени
audit_by_name = {}
for md_file in AUDIT_DIR.glob('*.md'):
    text = md_file.read_text(encoding='utf-8')
    j = extract_json_from_md(text)
    if j and 'id' in j:
        audit_by_name[j['id']] = j

# Обновляем добавок
updated = 0
for s in data:
    name = s.get('name')
    if name in audit_by_name:
        a = audit_by_name[name]
        # Копируем поля аудита
        for key in ['category', 'verdict', 'grade', 'effect_outcome', 'caution', 'key_sources', 'updated']:
            if key in a:
                s[key] = a[key]
        updated += 1

DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'обновлено {updated}/81 добавок в docs/data.json')
print(f'пропущено: {[s["name"] for s in data if s["name"] not in audit_by_name]}')
