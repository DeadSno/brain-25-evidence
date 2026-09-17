import pathlib, re

# ===== script.js =====
p = pathlib.Path('docs/script.js')
t = p.read_text(encoding='utf-8')

# ---------- Пачка 1: точки грейда ----------
# 1.1 Удалить блок DOT_FILL/DOT_COLOR/DOT_TIP/комментарий "5-точечный бейдж"
t = re.sub(
    r"// ===== v2\.6: 5-точечный бейдж доверия[^=]*?const DOT_TIP = [^\n]*\n",
    "",
    t,
    flags=re.DOTALL
)

# 1.2 Удалить функцию gradeDots целиком
t = re.sub(
    r"function gradeDots\(s\) \{[^}]*\}\s*\n",
    "",
    t
)

# 1.3 Удалить вызовы + gradeDots(s) (в карточке и в модалке)
t = t.replace(" + gradeDots(s) +", " +")
t = t.replace("+ gradeDots(s) +", "+")

# ---------- Пачка 2: группировка модалки ----------
# 2.1 Добавить CARD_GROUPS после CARDBLOCKS
card_groups_def = """

const CARD_GROUPS = [
  { title: '📋 Основное', blocks: ['what','who','works','evidence'] },
  { title: '💊 Как принимать', blocks: ['how','onset','notwho'] },
  { title: '⚠️ Осторожно', blocks: ['conflicts','friends','ul'] },
  { title: '📚 Дополнительно', blocks: ['food','official','shop','myths'] }
];
"""
# Вставляем после объявления CARDBLOCKS (перед function renderConflicts)
t = t.replace(
    "\nfunction renderConflicts(s) {",
    card_groups_def + "\nfunction renderConflicts(s) {"
)

# 2.2 Переписать renderCardBlocks — рендерить по группам
old_render = """function renderCardBlocks(s) {
  return '<div class="cblocks">' + CARDBLOCKS.map(b =>
    '<div class="cblock" data-block-key="' + b.key + '"><h4>' + b.title + '</h4><div class="cbbody">' +
    (b.get(s) || BLOCK_EMPTY) + '</div></div>').join('') + '</div>';
}"""
new_render = """function renderCardBlocks(s) {
  return '<div class="cblocks">' + CARD_GROUPS.map(g => {
    const blocksHtml = g.blocks.map(k => {
      const b = CARDBLOCKS.find(x => x.key === k);
      if (!b) return '';
      const content = b.get(s) || BLOCK_EMPTY;
      const cls = (b.get(s)) ? 'cblock' : 'cblock cbEmpty';
      return '<div class="' + cls + '" data-block-key="' + b.key + '"><h4>' + b.title + '</h4><div class="cbbody">' + content + '</div></div>';
    }).join('');
    return '<div class="cgroup"><div class="cgTitle">' + g.title + '</div>' + blocksHtml + '</div>';
  }).join('') + '</div>';
}"""
t = t.replace(old_render, new_render)

# ---------- Пачка 3: фильтр пустых строк в сравнении ----------
# Находим const rows = [...] и добавляем .filter после
t = re.sub(
    r"(\[.*?\['\\\\u26A0 пёЏ РћСЃС‚РѕСЂРѕР¶РЅРѕ'.*?\]\s*\])",
    r"\1.filter(r => !((r[1] == null || r[1] === '—' || r[1] === '') && (r[2] == null || r[2] === '—' || r[2] === '')))",
    t
)
# Fallback: ищем по структуре массива строк
t = re.sub(
    r"(const rows = \[\s*(?:\[[^\]]*\],\s*)+\[[^\]]*\]\s*\]);",
    r"\1.filter(r => !((r[1] == null || r[1] === '—' || r[1] === '') && (r[2] == null || r[2] === '—' || r[2] === '')));",
    t
)

# ---------- Пачка 4: радар сравнения — убрать 5-ю ось ----------
# Убираем null из rawVals
t = t.replace(
    """    s.trends || 0,
    null ];""",
    "    s.trends || 0 ];"
)
# Убираем 5-е значение и условие в prof
t = re.sub(
    r"pctile\(r\[3\], BASE_FOR_PCT\.map\(x => x\.trends\)\),\s*0 // [^\n]*\n\s*\]\.map\(\(p, i\) => \{\s*if \(i === 4 && r\[4\] != null\) return 100 - p;\s*return p;",
    "pctile(r[3], BASE_FOR_PCT.map(x => x.trends))\n    ];\n  return prof;",
    t
)

p.write_text(t, encoding='utf-8')
print('✓ script.js: 4 пачки правок применены')

# ===== style.css =====
c = pathlib.Path('docs/style.css')
css = c.read_text(encoding='utf-8')

# Удалить CSS точек грейда
css = re.sub(r"\.gdots\{[^}]+\}\s*", "", css)
css = re.sub(r"\.gdots i\{[^}]+\}\s*", "", css)
css = re.sub(r"\.gdots i\.on\{[^}]+\}\s*", "", css)
css = re.sub(r"\.vwait\{[^}]+\}\s*", "", css)

# Удалить CSS для мёртвого price-блока
css = re.sub(r'\.cblock\[data-block-key="price"\]\s*h4\{[^}]+\}\s*', "", css)

# Добавить CSS для групп модалки
group_css = """
.cgroup{margin-bottom:1.2rem}
.cgTitle{font-size:1rem;font-weight:700;padding:.5rem .8rem;margin-bottom:.4rem;
  background:var(--card-bg);border-left:3px solid var(--accent);border-radius:4px;
  opacity:.9}
"""
if '.cgroup{' not in css:
    css = css.rstrip() + "\n" + group_css

c.write_text(css, encoding='utf-8')
print('✓ style.css: убраны точки, добавлены группы')
