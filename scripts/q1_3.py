import pathlib, re
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')

new_prof = """  const prof = s => {
    const science = pctile(s.scienceIndex || 0, BASE_FOR_PCT.map(x => x.scienceIndex));
    const maBase = pctile(s.metaCount || 0, BASE_FOR_PCT.map(x => x.metaCount));
    let verified = 0;
    if ((s.key_sources || []).length) verified += 50;
    if (s.grade) verified += 25;
    if (s.verdict && s.verdict !== 'ждёт верификации') verified += 25;
    const fields = ['about','who_needs','onset','myths','food_sources','guidelines','how_to_choose'];
    const filled = fields.filter(f => (s[f] || '').length > 0).length;
    const completeness = Math.round((filled / fields.length) * 100);
    return [science, maBase, verified, completeness];
  };
"""
t2, n = re.subn(r"  const rawVals = s => \[[\s\S]*?\n  \};\n", new_prof, t, count=1)
assert n == 1, 'блок rawVals/prof не найден'
t = t2
assert t.count('rawVals') == 0, 'rawVals остался'

old_labels = "const PROF_LABELS = ['Наука', 'База МА', 'Спрос', 'Интерес'];"
assert old_labels in t, 'PROF_LABELS не найдены'
t = t.replace(old_labels, "const PROF_LABELS = ['Наука', 'База МА', 'Верифицированность', 'Полнота карточки'];")

old_map = "labels: PROF_LABELS.map(l => l + ' (нормировано по базе)'),"
assert old_map in t, 'строка labels не найдена'
t = t.replace(old_map, "labels: ['Наука (перцентиль по базе)', 'База МА (перцентиль по базе)', 'Верифицированность (0-100)', 'Полнота карточки (0-100)'],")

p.write_text(t, encoding='utf-8')
print('Q1.3: радар = 4 честные оси, 5-я точка-призрак убита')
