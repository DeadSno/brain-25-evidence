import re
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
OUT = Path(__file__).resolve().parents[1] / "docs" / "changelog_public.html"

entries = []
current_version = None
current_date = None
current_changes = []

for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
    if line.startswith("## ["):
        if current_version:
            entries.append((current_version, current_date, current_changes))
        m = re.match(r"## \[(.*?)\] — (.*)", line)
        if m:
            current_version, current_date = m.groups()
            current_changes = []
    elif line.startswith("- "):
        current_changes.append(line[2:])

if current_version:
    entries.append((current_version, current_date, current_changes))

html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Журнал правок</title>
<link rel="stylesheet" href="style.css">
<script>
try {
  if (localStorage.getItem('theme') !== 'light') {
    document.addEventListener('DOMContentLoaded', function () {
      document.body.classList.add('dark');
      var b = document.getElementById('themeToggle');
      if (b) b.textContent = '☀️ Светлая тема';
    });
  }
} catch (e) {}
</script>
</head>
<body>
<header>
  <h1><a href="index.html" style="color:inherit;text-decoration:none" title="На главную">📋 Журнал правок</a></h1>
  <div class="hdr">
    <a class="btn" href="index.html">← Назад к дашборду</a>
    <button id="themeToggle">🌙 Тёмная тема</button>
  </div>
</header>
<table class="changelog">
<thead><tr><th>Дата</th><th>Версия</th><th>Что изменилось</th></tr></thead>
<tbody>
"""

for version, date, changes in reversed(entries):
    html += f"<tr><td>{date}</td><td>{version}</td><td><ul>"
    for change in changes:
        html += f"<li>{change}</li>"
    html += "</ul></td></tr>\n"

html += """</tbody>
</table>
<footer style="margin-top:2rem;padding-top:1rem;border-top:1px solid var(--border);font-size:.8rem;opacity:.75">
  <p><a href="index.html" style="color:inherit">← Дашборд «БАДы: цена vs наука»</a></p>
  <p>v2.5 · источники: PubMed, OpenAlex, Wildberries, Google Trends, Wikimedia</p>
</footer>
<script>
const $ = id => document.getElementById(id);
$('themeToggle').onclick = () => {
  const on = !document.body.classList.contains('dark');
  document.body.classList.toggle('dark', on);
  $('themeToggle').textContent = on ? '☀️ Светлая тема' : '🌙 Тёмная тема';
  localStorage.setItem('theme', on ? 'dark' : 'light');
};
</script>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"changelog_public.html: {len(entries)} versions")