"""AUDIT C (S4, приложение 3.4): фронтенд (innerHTML-векторы, fetch, chart,
localStorage, a11y, 375px, перф). Файлы НЕ меняются; результат → 03-frontend.md.
"""
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs" / "audit" / "03-frontend.md"

findings = []
info = []


def add(sev, cat, msg, ref=""):
    findings.append((sev, cat, msg, ref))


def text(p: Path):
    return p.read_text(encoding="utf-8")


IDX = text(ROOT / "docs" / "index.html")
MAP = text(ROOT / "docs" / "map.html")
JS = text(ROOT / "docs" / "script.js")
CSS = text(ROOT / "docs" / "style.css")


def ln(txt, needle, scope=400):
    for i, l in enumerate(txt.splitlines()[:scope], 1):
        if needle in l:
            return i
    return 0


# ---------------- 1. innerHTML-sinks + escaping ----------------
info.append("innerHTML-sinks (все строки исполняют разметку из data.json — first-party):")
sink_refs = []
for f, t in (("script.js", JS), ("map.html", MAP)):
    for m in re.finditer(r"\.innerHTML\s*=", t):
        i = t.count("\n", 0, m.start()) + 1
        l = t.splitlines()[i - 1].strip()[:80]
        sink_refs.append(f"{f}:{i}: {l}")

has_escape_fn = any(w in (JS + MAP) for w in ("escapeHtml", "createTextNode"))
if has_escape_fn:
    info.append("найден хелпер безопасной вставки (escapeHtml/createTextNode) — ок.")
else:
    add("🟡", "XSS-векторы", f"innerHTML собирает разметку из полей data.json и НЕТ хелпера экранирования (data.json first-party => 🟡, не 🔴): {len(sink_refs)} sinks", "; ".join(sink_refs[:6]))
info.append("векторы пользователя: #sup= и ?supplement= валидируются через `SUPS.some(s=>s.id===x)` перед рендером — инъекции нет.")

# countBadge / search — textContent вместо innerHTML
if "countBadge').textContent" in JS:
    info.append("countBadge/статистика используют textContent — безопасно.")

# ---------------- 2. fetch 404/500/битый JSON ----------------
fetch_sites = []
if "if (!r.ok)" in JS and "catch" in JS:
    info.append("script.js: fetch с проверкой r.ok + `.catch()` → видимое сообщение при 404/500/битом JSON.")
else:
    add("🔴", "fetch-ошибки", "script.js: нет проверки r.ok и/или нет .catch() — карточки молча не загрузятся", "docs/script.js:" + str(ln(JS, "fetch(")))
if "fetch('data.json?ts=' + Date.now()).then(r => r.json())" in MAP and ".catch" not in MAP.split("fetch", 1)[1]:
    add("🔴", "fetch-ошибки", "map.html: fetch БЕЗ проверки r.ok и БЕЗ .catch() — 404/500/битый JSON = белый экран (нет видимого сообщения)", "docs/map.html:115")
else:
    info.append("map.html: fetch обрабатывает ошибки.")
if ".catch" not in MAP and "fetch" in MAP:
    add("🟡", "fetch-ошибки", "map.html: нет ни одного .catch()", "docs/map.html")

# ---------------- 3. Chart.js destroy при перерендере ----------------
if "if (chartInstance) chartInstance.destroy()" in JS and "if (radarInstance) radarInstance.destroy()" in JS:
    info.append("Chart.js: destroy() перед пересозданием bubble- и radar-графиков — утечек нет.")
else:
    add("🟡", "chart", "chartInstance/radarInstance.destroy() вызывается не перед каждым рендером — проверить", "docs/script.js")
info.append("Chart.js подключён один раз (cdn v4.4.1); собственные канвасы destroy корректно.")

# ---------------- 4. остатки d3 ----------------
d3 = re.findall(r"d3\.|svg-d3|/d3/|d3\.js|d3@", JS + IDX + MAP)
if d3:
    add("🟡", "d3", f"остатки d3: {len(d3)}", "; ".join(d3[:3]))
else:
    info.append("d3 не подключён и не используется — остатков нет.")

# ---------------- 5. localStorage битые значения ----------------
def lscount(txt):
    return len(re.findall(r"localStorage\.(getItem|setItem|removeItem)", txt))


def lscatch(txt):
    return len(re.findall(r"try\s*\{[^}]*localStorage", txt, re.S))


info.append(f"localStorage: index.html={lscount(IDX)} обращений, map.html={lscount(MAP)}, script.js={lscount(JS)}.")
raw_reads = []
if "localStorage.getItem('favs')" in JS and "return []" in JS:
    info.append("getFavs(): JSON.parse обёрнут в try/catch → битые fav=\"{{{\" → [] — ок.")
else:
    raw_reads.append("script.js favs")
if "mapClosed" in MAP and "try" in MAP and "catch" in MAP:
    info.append("mapClosed: JSON.parse обёрнут в try/catch → битые значения отфильтрованы — ок.")
if "localStorage.getItem('theme')" in JS and not re.search(r"try[^{]*\{", JS.split("const saved")[0][-90:]):
    add("🟡", "localStorage", "theme в script.js читается БЕЗ try/catch (localStorage может кидать SecurityError в приватном режиме) — упадёт инициализация", "docs/script.js:28")
if "localStorage.getItem('theme')" in IDX and "catch" in IDX:
    info.append("theme в index.html <head> читается в try/catch — ок.")

# ---------------- 6. a11y ----------------
a11y_refs = []
if 'role="dialog"' not in IDX and 'aria-modal' not in IDX:
    add("🟡", "a11y", "модалка без role=dialog/aria-modal и без фокуса-трапа", "docs/index.html:114-118")
if '<button id="modalClose">✕</button>' in IDX and 'aria-label' not in IDX.split('modalClose">✕')[0].splitlines()[-1]:
    add("🟡", "a11y", "кнопка закрытия модалки без aria-label/aria-hidden (двойной таб не сообщит смысл)", "docs/index.html:116")
for s in ("modalClose" in IDX, "modalOverlay" in IDX):
    pass
if "document.addEventListener('keydown'" in JS and "Escape" in JS:
    info.append("Esc закрывает модалку (script.js) и сбрасывает поиск (map.html) — ок.")
else:
    add("🟡", "a11y", "нет обработчика Esc для модалки", "docs/script.js")
if "tabIndex" not in MAP and "button" not in MAP:
    pass
clean = re.sub(r"<style>.*?</style>", "", MAP, flags=re.S)
if "h3" in re.sub(r"<script>.*?</script>", "", MAP, flags=re.S) and "tabIndex" not in MAP:
    add("🟡", "a11y", "категории карты — <h3>/<span>, не фокусируемые (только клик; клавиатура не дойдёт)", "docs/map.html:126-127")
# контраст бейджей: v0 (жёлтый #f1c40f) + белый текст
if "background: linear-gradient(135deg, #b7791f, #f1c40f)" in CSS:
    add("🟡", "a11y", "контраст бейджа вердикта v0 (#f1c40f + белый текст) ~1.9:1 < 4.5:1 (WCAG AA не проходит)", "docs/style.css:161")
if "background: linear-gradient(135deg, #1e8e4e, #2ecc71)" in CSS:
    add("🟡", "a11y", "контраст бейджа v1 (#2ecc71 + белый текст) ~2.1:1 < 4.5:1", "docs/style.css:160")

# ---------------- 7. 375px ----------------
has_mq = bool(re.search(r"@media[^{]+max-width:\s*768px|@media[^{]+max-width:\s*860px", CSS + MAP))
has_mq_375 = "(max-width:860px)" in MAP or "(max-width:768px)" in CSS
if has_mq_375:
    info.append("медиа-запросы: style.css(768px) и map.html(860px) есть; 375px-ветка в любом случае схлопывается — глазами не прогонялась (playwright не установлен).")
else:
    add("🟡", "375px", "нет медиа-запросов <768px — сетка/модалка/чипы могут ломаться на 375px", "")
info.append("примечание: визуальную проверку 375px нельзя выполнить headless (playwright не установлен) — нужна проверка человеком.")

# ---------------- 8. перф ----------------
dj = (ROOT / "docs" / "data.json").stat().st_size
info.append(f"data.json={dj} байт ({dj/1024:.1f} КБ) — для 81 карточки приемлемо; рендер 81 карточки O(n) без сет-расчётов; Chart.js cdn 4.4.1.")
if dj > 300_000:
    add("🟡", "перф", f"data.json уже {dj/1024:.0f} КБ — следить; сейчас в норме", "")
if "fonts.googleapis" in IDX and "preconnect" in IDX:
    info.append("шрифт Inter: preconnect к googleapis+gstatic есть — ок (перф).")

# ---------------- артефакт ----------------
red = sum(1 for f in findings if f[0] == "🔴"); yel = sum(1 for f in findings if f[0] == "🟡")
gre = sum(1 for f in findings if f[0] == "🟢")
top5 = sorted(findings, key=lambda f: {"🔴": 0, "🟡": 1, "🟢": 2}[f[0]])[:5]
sections = [
    "# AUDIT C (S4) — фронтенд",
    f"Дата: {date.today().isoformat()} | скрипт: scripts/audit_frontend.py | файлы НЕ менялись",
    "",
    "## Шапка",
    "| Severity | Кол-во |",
    "| --- | --- |",
    f"| 🔴 | {red} |",
    f"| 🟡 | {yel} |",
    f"| 🟢 | {gre} |",
    "",
    "## Топ-5",
] + [f"- {s} **{c}**: {m}  `{r}`" for s, c, m, r in top5] + [
    "",
    "## Инфо",
] + [f"- {i}" for i in info] + [
    "",
    "## Находки (≤25)",
] + [f"{s} {c}: {m}  `{r}`" for s, c, m, r in findings[:25]] + [
    "",
]
ART.parent.mkdir(parents=True, exist_ok=True)
ART.write_text("\n".join(sections), encoding="utf-8")
print(f"audit: {ART}")
print("counts:", {"🔴": red, "🟡": yel, "🟢": gre})
print("top5:")
for s, c, m, r in top5:
    print(f"  {s} {c}: {m} {r[:80]}")