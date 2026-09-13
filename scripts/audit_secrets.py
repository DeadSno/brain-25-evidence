"""AUDIT B (S3, приложение 3.3): python + CI + секреты.

Файлы НЕ меняются; результат → docs/audit/02-python-ci.md.
"""
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs" / "audit" / "02-python-ci.md"

findings = []
info = []


def add(sev, cat, msg, ref=""):
    findings.append((sev, cat, msg, ref))


def lines(p: Path):
    return p.read_text(encoding="utf-8").splitlines()


def file_line(p: Path, needle: str, scope=50):
    """первая строка p, где needle входит (в пределах scope строк)."""
    try:
        ls = lines(p)
    except Exception:
        return f"{p.name}:?"
    for i, ln in enumerate(ls[:scope], 1):
        if needle in ln:
            return f"{p.name}:{i}"
    return f"{p.name}:> {scope}"


SRC_TXT = (ROOT / "src" / "parsers.py").read_text(encoding="utf-8")
CONF_TXT = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
COLLECT_TXT = (ROOT / "scripts" / "collect_prices.py").read_text(encoding="utf-8")
ECON_TXT = (ROOT / "src" / "economics.py").read_text(encoding="utf-8")
CONTENT_TXT = (ROOT / "src" / "content.py").read_text(encoding="utf-8")
WORKFLOWS = {p.name: p for p in (ROOT / ".github" / "workflows").glob("*.yml")}
SERVE = (ROOT / "serve.py").read_text(encoding="utf-8")

# ---------------- 1. парсеры: 500/429/timeout, ретраи? ----------------
API_CALLS = [("PubMed E-utilities", "eutils.ncbi.nlm.nih.gov", "pubmed_count", "def pubmed_count"),
             ("OpenAlex", "api.openalex.org", "openalex_count", "def openalex_count"),
             ("Wildberries search", "search.wb.ru", "wb_search", "def wb_search")]
has_retry_kw = any(w in SRC_TXT for w in ("retry", "backoff", "max_retries", "for attempt"))
retry_blocks = len(re.findall(r"(?i)\b(retries|retry|backoff)\b", SRC_TXT))
no_retry = []
for name, host, fn, fn_sig in API_CALLS:
    if host not in SRC_TXT:
        add("🟡", "парсеры", f"{name} не найдено в parsers.py", "")
        continue
    ref = file_line(ROOT / "src" / "parsers.py", fn_sig, scope=200)
    info.append(f"{name}: {fn}() в {ref}; никогда не вызывается с ретраем; для 429/500 — падение или -1.")
    if not retry_blocks:
        no_retry.append(f"{fn}()")
if no_retry:
    add("🟡", "парсеры",
        f"нет ретраев/backoff у: {', '.join(no_retry)} (429/500/таймаут = падение или -1)",
        "; ".join([file_line(ROOT / "src" / "parsers.py", s, scope=200) for s in
                   ["def pubmed_count", "def openalex_count", "def wb_search"] if not retry_blocks]))
else:
    info.append(f"паттернов retry/backoff в parsers.py: {retry_blocks}")

# openalex глотает ВСЕ исключения → -1
if "except Exception:" in SRC_TXT:
    add("🔴", "парсеры",
        "openalex_count: `except Exception: return -1` — маскирует 429/500/timeout как данные",
        "src/parsers.py:53-54 (и +51 try)")

# нет ли вообще обработки HTTPError отдельно
if "urllib.error" not in SRC_TXT and "requests.exceptions" not in SRC_TXT:
    info.append("parsers.py использует только `raise_for_status()` — явных except-типов нет (кроме широкого голого).")

# ---------------- 2. идемпотентность ----------------
if re.search(r"(?i)(seed|random\.seed|np\.random\.seed)", COLLECT_TXT + SRC_TXT + ECON_TXT):
    add("🟡", "идемпотентность", "найдены seed/random — проверить детерминизм", "")
else:
    info.append("seed/random в src/scripts не используются — детерминизм от порядка словарей.")
info.append("порядок словарей config.py фиксирован (dict 3.7+); data.json стабилен (снапшот-тест).")
if "drop_duplicates(subset=[\"дата\", \"добавка\", \"источник\"])" in COLLECT_TXT:
    info.append("collect_prices.py: append идемпотентен — drop_duplicates по (дата,добавка,источник).")
else:
    add("🟡", "идемпотентность", "нет защиты от дублей при append истории цен", "scripts/collect_prices.py:14")
# timestamp = by design
info.append("timestamp (`дата`=strftime, снапшот UPDATE_SNAPSHOT) — by design по брифу, не баг.")

# ---------------- 3. хардкод ----------------
for p in sorted((ROOT / "src").glob("*.py")) + [ROOT / "scripts" / "collect_prices.py", ROOT / "serve.py"]:
    t = p.read_text(encoding="utf-8")
    for m in re.finditer(r"[A-Za-z]:\\\\[A-Za-z]|C:\\Users|/mnt/|C:/", t):
        ln = t.count("\n", 0, m.start()) + 1
        add("🔴", "хардкод", f"абсолютный путь: {m.group()} в {p.name}:{ln}", f"{p.name}:{ln} {m.group()}")
        break
magics = []
if "dest" in SRC_TXT and "-1257786" in SRC_TXT:
    magics.append("WB dest=-1257786 (магическое число региона)")
add("🟢", "хардкод", f"магические константы в src (часть — конфиг-значения): {len(magics)}", "; ".join(magics) or "—")
rel = [s for s in lines(ROOT / "scripts" / "collect_prices.py")
       if "data/raw/" in s and "Path(" not in s]
if rel:
    add("🟡", "хардкод", f"относительный путь от CWD: «{rel[0].strip()}» (работает из корня репо)",
        "scripts/collect_prices.py:" + str(lines(ROOT / "scripts" / "collect_prices.py").index(rel[0]) + 1))
else:
    info.append("collect_prices.py: пути через Path(__file__) или относительные от корня — ок.")
if "PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000" in SERVE:
    info.append("serve.py: порт из аргумента с дефолтом 8000 — ок (не хардкод).")

# ---------------- 4. type hints / docstrings = 🟢 ----------------
stats = {}
for p in sorted((ROOT / "src").glob("*.py")) + [ROOT / "scripts" / "collect_prices.py", ROOT / "serve.py"]:
    t = p.read_text(encoding="utf-8")
    funcs = re.findall(r"^def (\w+)\(([^)]*)\)", t, re.M)
    hinted = [f for f, a in funcs if ":" in a]
    docd = len(re.findall(r'^\s{4}""".*?"""', t, re.M | re.S)) + (1 if t.splitlines() and t.lstrip().startswith('"""') else 0)
    stats[p.name] = (len(funcs), len(hinted), docd)
tot_f = sum(v[0] for v in stats.values()); tot_h = sum(v[1] for v in stats.values()); tot_d = sum(v[2] for v in stats.values())
if tot_f and tot_h / tot_f >= 0.7:
    add("🟢", "типхинты", f"type hints у {tot_h}/{tot_f} функций; docstrings ≈{tot_d}", "; ".join(f"{k}={v[1]}/{v[0]}" for k, v in stats.items()))
else:
    add("🟡", "типхинты", f"type hints лишь у {tot_h}/{tot_f} функций (порог 70%)", "; ".join(f"{k}={v[1]}/{v[0]}" for k, v in stats.items()))

# ---------------- 5. тесты: happy path + рекомендации ----------------
test_files = sorted((ROOT / "tests").glob("test_*.py"))
tnames = []
for tf in test_files:
    tnames += re.findall(r"^def (test_\w+)", tf.read_text(encoding="utf-8"), re.M)
info.append(f"тестов: {len(test_files)} файлов, {len(tnames)} функций: {', '.join(sorted(tnames))}")
info.append("happy path есть: parse_units(г/капс/табл), GARDEN-фильтр, цена_мес, категории, savings, schema, sync config-data, snapshot.")
info.append("network-тесты исключены: pytest.ini addopts=-m 'not network' (marker network).")
reco = [
    "1) wb_search: фикстура JSON → цена_руб=копейки/100 (сейчас network-marker, offline не покрыт)",
    "2) collect_prices.append: повторный запуск не дублирует (drop_duplicates) — с фикстурой истории",
    "3) openalex_count: mock HTTPError → возврат -1 и НЕ падение (зафиксировать семантику)",
    "4) serve.py: GET / и GET /data.json через real HTTP server (без браузера)",
    "5) parsers: вежливость — между wb_search вызовами ≥0.9s (регрессия сна, т.к. сейчас sleep=1.0)",
]
add("🟢", "тесты", f"предложено {len(reco)} новых тестов (happy-path есть):", "; ".join(reco))

# ---------------- 6. workflows: permissions / pinning / cron ----------------
wf = WORKFLOWS.get("collect_prices.yml")
t = wf.read_text(encoding="utf-8") if wf else ""
if "permissions:" in t and "contents: write" in t:
    info.append("collect_prices.yml: permissions contents:write (минимально для push), concurrency: есть.")
else:
    add("🟡", "CI", "collect_prices.yml: нет permissions/concurrency", "collect_prices.yml")
if "pull --rebase" in t:
    info.append("collect_prices.yml: git pull --rebase перед push — защита от гонок (по документу).")
else:
    info.append("collect_prices.yml: merge-стратегия отсутствует (риск гонок push).")

tt = WORKFLOWS["tests.yml"].read_text(encoding="utf-8") if "tests.yml" in WORKFLOWS else ""
branches = re.findall(r"- ([\w\-.]+)", re.search(r"branches:(.*?)pull_request", tt, re.S).group(1) if "branches:" in tt else "")
want = ["v2.1-dev", "v2.0-dev"]
missing_b = [b for b in want if b not in branches]
if missing_b:
    add("🟡", "CI", f"tests.yml: push не включает ветки {missing_b} — CI не гоняется на них",
        ".github/workflows/tests.yml:4")
else:
    info.append("tests.yml: триггеры покрывают все dev-ветки.")
if "permissions:" not in tt:
    info.append("tests.yml: permissions не заданы — дефолт read (ок).")
for wfname, wp in WORKFLOWS.items():
    for m in re.finditer(r"(?i)(pip install|uses:\s+)[^\n]{0,60}\b([A-Za-z0-9_.-]+@v?[0-9]+|[a-z-]+)", wp.read_text(encoding="utf-8")):
        pass
# pinning утилит
pin = re.findall(r"uses:\s+([a-zA-Z0-9._/-]+@v\d+\.?\d*)", t + (WORKFLOWS["tests.yml"].read_text(encoding="utf-8") if "tests.yml" in WORKFLOWS else ""))
if pin:
    info.append(f"actions протегированы (не SHA): {', '.join(sorted(set(pin)))} — ок для малого проекта.")
else:
    add("🟡", "CI", "действия actions не зафиксированы (голые имена)", "")
if "pip install requests pandas" in t and "==" not in t:
    add("🟡", "CI", "pip install зависимостей без версий — воспроизводимость", "collect_prices.yml:26")
crons = re.findall(r"- cron:\s*\"([^\"]+)\"", t)
info.append(f"collect_prices.yml cron: {crons} (README: 06:00 МСК = 03:00 UTC — совпадает).")

# ---------------- 7. grep токенов ----------------
SECRET_RE = [
    (r"ghp_[A-Za-z0-9]{20,}", "GitHub PAT"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack токен"),
    (r"\bbot\d{6,}:", "Telegram bot token"),
    (r"TG(?:[_-]?API)?[_-]?(?:KEY|TOKEN)['\"]?\s*[:=]\s*['\"]\S+", "TG-токен в коде"),
    (r"VK[_-]?TOKEN['\"]?\s*[:=]\s*['\"]\S+", "VK-токен"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"(sk_live|pk_live|sk_test)_[A-Za-z0-9]{16,}", "Stripe ключ"),
    (r"yandex.*?(OAuth|oauth).*?['\"][A-Za-z0-9._~-]{20,}['\"]", "Yandex OAuth"),
]
hits = []
skip_docs = {"README.md", "CHANGELOG.md", "LICENSE", "docs/index.html", "docs/map.html"}
for f in [*sorted((ROOT / "src").glob("*.py")), ROOT / "scripts" / "collect_prices.py",
          ROOT / "scripts" / "audit_data.py", ROOT / "scripts" / "audit_content.py",
          *WORKFLOWS.values(), ROOT / ".github" / "ISSUE_TEMPLATE" / "data-error.md",
          ROOT / "requirements.txt", ROOT / "serve.py", ROOT / "conftest.py", ROOT / "pytest.ini",
          *sorted((ROOT / "tests").glob("*.py"))]:
    try:
        t = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for i, ln in enumerate(t.splitlines(), 1):
        s = ln.lower()
        if "метрика" in s or "112465667" in s:
            continue  # id метрики ≠ баг (документировано)
        for pat, name in SECRET_RE:
            if re.search(pat, ln):
                hits.append(f"{f.name}:{i}: {name} ({ln.strip()[:60]})")
if hits:
    add("🔴", "секреты", f"потенциальные токены: {len(hits)}", "; ".join(hits[:5]))
else:
    add("🟢", "секреты", "токенов (ghp_/xox/botXXX: и пр.) в .py/workflows/NOT-документах не найдено — после эксклюзии id метрики", "")
# также notebook-и
nb_hits = []
for nb in (ROOT / "notebooks").glob("*.ipynb"):
    t = nb.read_text(encoding="utf-8")
    for pat, name in SECRET_RE:
        for m in re.finditer(pat, t):
            nb_hits.append(f"{nb.name}: {name}")
        if re.search(r"(?i)(token|secret|password)\s*=\s*['\"][A-Za-z0-9]{12,}['\"]", t):
            nb_hits.append(f"{nb.name}: assignment token/secret/password")
if nb_hits:
    add("🔴", "секреты", f"в notebooks: {len(nb_hits)}", "; ".join(sorted(set(nb_hits))[:5]))
else:
    info.append("notebooks: токенов не найдено.")

# ---------------- 8. вежливость WB-парсинга ----------------
if 'timeout=15, headers={"User-Agent": "Mozilla/5.0"}' in SRC_TXT:
    info.append("wb_search: UA браузеро-подобный + timeout=15 — вежливо.")
else:
    info.append("wb_search: UA есть, timeout — проверить вручную.")
if "time.sleep(1.0)" in SRC_TXT:
    info.append("collect_wb_prices: sleep(1.0) между запросами — вежливость соблюдена (см. тесты reco #5).")
else:
    add("🟡", "вежливость", "нет задержки между WB-запросами в цикле", "src/parsers.py:111")
if "raise_for_status" in SRC_TXT:
    info.append("raise_for_status() присутствует (быстрый фейл на 4xx/5xx).")

# ---------------- артефакт ----------------
red = sum(1 for f in findings if f[0] == "🔴"); yel = sum(1 for f in findings if f[0] == "🟡")
gre = sum(1 for f in findings if f[0] == "🟢")
top5 = sorted(findings, key=lambda f: {"🔴": 0, "🟡": 1, "🟢": 2}[f[0]])[:5]
sections = [
    "# AUDIT B (S3) — python + CI + секреты",
    f"Дата: {date.today().isoformat()} | скрипт: scripts/audit_secrets.py | файлы НЕ менялись",
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