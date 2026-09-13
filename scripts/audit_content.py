"""AUDIT D (S2, приложение 3.2): тексты, термины, числа, даты, дисклеймер, ссылки.

Файлы НЕ меняются; STDOUT-результат → docs/audit/04-content.md.
"""
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs" / "audit" / "04-content.md"

findings = []   # (sev, cat, msg, ref)
info = []


def add(sev, cat, msg, ref=""):
    findings.append((sev, cat, msg, ref))


def line_ref(p: Path, needle: str, ctx: int = 12):
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return "unreadable"
    for i, ln in enumerate(lines, 1):
        if needle in ln:
            return f"{p.name}:{i}"
    return f"{p.name}:?"  # не верифицировано, точная строка не найдена


# ---------------- текстовые корпуса ----------------
ui = {}
for f in ("docs/index.html", "docs/map.html", "docs/script.js"):
    ui[f] = (ROOT / f).read_text(encoding="utf-8")
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
readme = (ROOT / "README.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


# ---------------- 1. термины ----------------
terms = {
    "вердикт": "index/map/script",
    "статус": "альтернатива «вердикту»?",
    "ценность": "index/script",
    "Value Score": "англ. вариант «ценности»?",
}
for t, where in terms.items():
    hits_ui = sum(ln.count(t) for f in ui.values() for ln in f.splitlines())
    hits_data = sum((d.get("verdict") or "").count(t) for d in data)
    if hits_ui + hits_data == 0 and t in ("статус", "Value Score"):
        info.append(f"термин «{t}» в UI/данных НЕ встречается ({where}): согласовано.")
    else:
        info.append(f"термин «{t}»: UI={hits_ui}, data.verdict={hits_data} ({where}).")

# рассинхрон вердикт/статус где-либо в UI
both = []
for f, txt in ui.items():
    if "статус" in txt and "вердикт" in txt:
        both.append(f)
if both:
    add("🟡", "термины", f"«вердикт» И «статус» в одном файле: {both}", "")
else:
    info.append("вердикт/статус: нигде не смешаны в одном UI-файле.")

# «ценность/Value Score»: есть ли оба
if any("Value Score" in t for t in ui.values()) or "Value Score" in readme:
    add("🟡", "термины", "«Value Score» встречается — есть ли «ценность»-вариант рядом?", "README/docs/*.html")
else:
    info.append("Value Score не используется; единый термин «ценность».")


# ---------------- 2. числа 41/81 ----------------
seen_mismatch = []
for f, txt in ui.items():
    for pat in (r"\b41\b добав", r"41 добавок", r"— 41", r"для 41"):
        for m in re.finditer(pat, txt):
            ln = txt.count("\n", 0, m.start()) + 1
            seen_mismatch.append(f"{f}:{ln}: {m.group()}")
if seen_mismatch:
    add("🔴", "числа 41/81", f"устаревшее «41» в UI/описаниях: {len(seen_mismatch)} шт", "; ".join(seen_mismatch[:6]))
else:
    info.append("«41 добавка» в UI не найдено.")

if "supplements-41" in readme:
    add("🔴", "числа 41/81", "README-бейдж supplements => 41 (а data.json=81)", "README.md:9")
if "version-v1.2" in readme:
    add("🔴", "числа 41/81", "README-бейдж version => v1.2 (текущий v2.0)", "README.md:8")
if "tests-17" in readme:
    add("🔴", "числа 41/81", "README-бейдж tests => 17 passed (сейчас 24+1 deselected)", "README.md:10")
if "41 добавк" in readme.split("# Что это и зачем")[0]:
    add("🔴", "числа 41/81", "README-шапка «для 41 ... добавки» / «из 41 добавки»", "README.md:3")
n41 = [m.start() for m in re.finditer(r"\b41\b", readme)]
if len(n41) > 5:
    add("🟡", "числа 41/81", f"в README ещё {len(n41)} упоминаний «41» (данные-раздел/method), см. файл", "README.md:132-140")


# ---------------- 3. даты ----------------
last_dates = {}
for f, txt in ui.items():
    for m in re.finditer(r"\b\d{2}\.\d{2}\.\d{4}\b|\bv?\d+,\s*\d{4}\b|\bv?1\.2\b", txt):
        last_dates.setdefault(f, set()).add(m.group())
for f, ds in last_dates.items():
    info.append(f"даты в {f}: {sorted(ds)}")

if "v2.0 • данные на 11.09.2026" not in ui.get("docs/index.html", ""):
    # футер может быть другим — собери реальный
    for m in re.finditer(r"(?:данные на|v[\d.]+)\s*[^\n<]*", ui.get("docs/index.html", "")):
        info.append(f"index.html футер: {m.group().strip()}")

# CHANGELOG-даты vs README
m_ch = re.findall(r"## \[([^\]]+)\] — (\d{4}-\d{2}-\d{2})", changelog)
info.append(f"CHANGELOG-блоки: {m_ch}")
if "v1.2" in readme and "2026-09-11" not in changelog[:80]:
    add("🟡", "даты", "README помечает данные как «v1.2, 09.09.2026», а last release в CHANGELOG — v2.0 (2026-09-11)", "README.md:132,295 vs CHANGELOG.md:1")
rg = re.search(r"v?[\d.]+,\s*\d{2}\.\d{2}\.\d{4}", readme)
if rg:
    add("🟡", "даты", f"README-подвал: «{rg.group()}» (версия/дата), может расходиться с v2.0", "README.md:295")


# ---------------- 4. дисклеймер ----------------
for page in ("docs/index.html", "docs/map.html"):
    txt = ui[page]
    if "Дисклеймер" in txt or "не являет" in txt or "не является медицинской" in txt:
        info.append(f"дисклеймер НА СТРАНИЦЕ {page}: есть.")
    else:
        add("🔴", "дисклеймер", f"на {page} дисклеймера на странице нет", page)
# модалки (script.js инжектит modalBody)
mo = ui["docs/script.js"]
if "не являет" not in mo and "медицинск" not in mo:
    add("🟡", "дисклеймер", "в модалках (script.js modalBody) дисклеймера/ссылки на него нет — только на странице", "docs/script.js:148-161")
else:
    info.append("дисклеймер встречается в script.js.")


# ---------------- 5. опечаточные паттерны ----------------
# 5a: двойные пробелы в СЕРЕДИНЕ строк (leading-отступы не считаются)
tot = 0; refs = []
for f, txt in ui.items():
    for i, ln in enumerate(txt.splitlines(), 1):
        if re.search(r"\S\s{2,}\S", ln):
            tot += 1
            if len(refs) < 5:
                refs.append(f"{f}:{i}")
if tot:
    add("🟡", "опечатки", f"двойной пробел в середине строки: {tot} вхождений", "; ".join(refs) or "не верифицировано")
else:
    info.append("двойных пробелов в середине строк UI нет (отступы не считаем).")

# 5b: баланс ёлочек в каждом файле
for f, txt in ui.items():
    o = txt.count("«"); c = txt.count("»")
    if o != c:
        add("🟡", "опечатки", f"несбалансированные ёлочки: «={o}, »={c}", f)
    else:
        info.append(f"ёлочки сбалансированы в {f} («={o}).")

# 5c: латиница внутри кириллического текста (данные и строки UI)
refs = []
for f, txt in ui.items():
    for i, ln in enumerate(txt.splitlines(), 1):
        if re.search(r"[а-яёА-ЯЁ][a-zA-Z]|[a-zA-Z][а-яёА-ЯЁ]", ln):
            sn = re.sub(r"\s{2,}", " ", ln).strip()
            refs.append(f"{f}:{i}: {sn[:90]}")
for d in data:
    for fld in ("name", "verdict", "category", "effects", "dosage", "forms", "caution", "course"):
        v = d.get(fld)
        if isinstance(v, list):
            v = " ".join(map(str, v))
        if v and re.search(r"[а-яёА-ЯЁ][a-zA-Z]|[a-zA-Z][а-яёА-ЯЁ]", str(v)):
            refs.append(f"data.json:{d['id']}.{fld}: {str(v)[:60]}")
seen = len(set(refs))
if seen:
    add("🟡", "опечатки", f"латиница в кириллическом тексте: {seen} уникальных кандидатов", "; ".join(sorted(set(refs))[:8]))
else:
    info.append("латиницы в кириллическом тексте не найдено.")

info.append("опечатко-паттерны: серединные 2+пробела, баланс ёлочек, латиница в кириллице (выборочно)")


# ---------------- 6. ссылки (HEAD→GET, UA, 2 ретрая, 429≠бита) ----------------
url_re = re.compile(r"https?://[^\s\"'<>()]+")
urls = set()
for f, txt in {**ui, "README.md": readme, "CHANGELOG.md": changelog}.items():
    for m in url_re.finditer(txt):
        u = m.group().rstrip(".,;)]}").strip('"')
        if u.startswith("http://localhost") or "www.w3.org/2000/svg" in u or u.endswith("svg%22"):
            continue  # инструкция локального запуска / SVG-namespace, не ссылки
        if "deadsno.github.io" in u:
            urls.add((f, u, "first-party"))
        elif "yandex.ru/metrika" in u or "mc.yandex.ru" in u:
            urls.add((f, u, "third-party-cdn"))
        elif "jsdelivr" in u or "googleapis" in u or "gstatic" in u:
            urls.add((f, u, "third-party-cdn"))
        elif "clinicaltrials.gov" in u and "about-api" in u:
            urls.add((f, u, "docs-api"))
        else:
            urls.add((f, u, "external"))

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
dead = []
rate = []
checked = 0
for f, u, kind in sorted(urls):
    code = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(u, headers=UA, method="HEAD")
            with urllib.request.urlopen(req, timeout=12) as r:
                code = r.status
            if code in (405, 403, 400):
                # fallback GET
                req = urllib.request.Request(u, headers=UA, method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=12) as r:
                        code = r.status
                except urllib.error.HTTPError as e:
                    code = e.code
            if code in (200, 301, 302, 303, 304, 307, 308):
                break
        except urllib.error.HTTPError as e:
            code = e.code
            if code != 429:
                break
        except urllib.error.URLError as e:
            code = f"DNR:{type(e.reason).__name__}"
            break
        except Exception as e:
            code = f"ERR:{type(e).__name__}"
            break
    checked += 1
    bot = any(h in u for h in ("t.me/share", "vk.com/share", "wildberries.ru"))
    if code == 429:
        rate.append(f"{f}: {u} (429, 2 ретрая исчерпаны)")
    elif bot:
        rate.append(f"{f}: {u} → {code} (бот-защита, не считается битой)")
    elif kind == "third-party-cdn" and code not in (200, 301, 302, 303, 304, 307, 308):
        rate.append(f"{f}: {u} → {code} (CDN не верифицировано)")
    elif code not in (200, 301, 302, 303, 304, 307, 308) or isinstance(code, str):
        dead.append(f"{f}: {u} → {code} [{kind}]")
    else:
        info.append(f"OK {code}: {u} ({kind})")

info.append(f"ссылки проверены: {checked} (HEAD→GET, UA, 2 ретрая; 429/бот-защита≠битые).")
if dead:
    add("🔴", "ссылки", f"мёртвые/ошибочные: {len(dead)}", "; ".join(dead[:8]))
if rate:
    add("🟡", "ссылки", f"не верифицировано ({len(rate)}): 429/бот-защита/CDN", "; ".join(rate[:4]))


# ---------------- артефакт ----------------
red = sum(1 for f in findings if f[0] == "🔴")
yel = sum(1 for f in findings if f[0] == "🟡")
gre = sum(1 for f in findings if f[0] == "🟢")
top5 = sorted(findings, key=lambda f: {"🔴": 0, "🟡": 1, "🟢": 2}[f[0]])[:5]

sections = [
    "# AUDIT D (S2) — тексты, термины, числа, даты, ссылки",
    f"Дата: {date.today().isoformat()} | скрипт: scripts/audit_content.py | файлы НЕ менялись",
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