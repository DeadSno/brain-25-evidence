"""AUDIT A (S1, приложение 3.1): карта проекта + данные data.json.

Механика: скрипт не меняет аудируемые файлы; STDOUT-дайджест в артефакт.
Запуск:  python scripts/audit_data.py
Артефакт: docs/audit/01-map-data.md
"""
import ast
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}
ARTS = ROOT / "docs" / "audit"
ART = ARTS / "01-map-data.md"

REQUIRED = ["id", "name", "code", "verdict", "category", "scienceIndex",
            "metaCount", "effects", "dosage", "mechs"]

findings = []  # (severity, category, message, ref)
info = []


def walk(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        yield rel

def lines_of(rel: Path) -> list[str]:
    try:
        return (ROOT / rel).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


# ---------------- 1. карта проекта ----------------
tree_lines = [str(p) for p in walk(ROOT)]
# дерево в вывод без лишних каталогов, прижать глубину для читаемости
tree = "\n".join(tree_lines)

# кто реально генерирует data.json (пофайлово: файл = генератор, если в нём
# встречаются и "data.json", и write-операция — в .ipynb они часто в разных строках)
gen_hits = []
for rel in walk(ROOT):
    if rel.suffix not in (".py", ".ipynb"):
        continue
    if rel.parts and rel.parts[0] in ("tests",):
        continue  # тесты пишут свой слепок, не docs/data.json
    if rel.name == "audit_data.py":
        continue  # сам инструмент аудита не в счёт
    body = lines_of(rel)
    has_json_ref = any('"data.json"' in ln or "data.json" in ln for ln in body)
    has_write = any(t in ln for ln in body for t in
                    ("write_text", "json.dumps(", "to_json", ".dump(", "open(", "savefig"))
    if has_json_ref and has_write:
        wr = next((f":{i}" for i, ln in enumerate(body, 1)
                   if any(t in ln for t in ("write_text", "json.dumps(", "to_json", ".dump("))), "")
        gen_hits.append(f"{rel}{wr} — генератор (data.json + write)")
if gen_hits:
    info.append(f"data.json ГЕНЕРИРУЕТСЯ в: {'; '.join(gen_hits[:8])}")
else:
    info.append("data.json: прямых генераторов в .py/.ipynb не найдено")

# мёртвый код (эвристика): верхнеуровневые def/class в src|scripts
def uncomment(ln: str) -> str:
    return ln.split("#", 1)[0].strip() if "#" in ln else ln.strip()

names_def = {}
for rel in walk(ROOT):
    if rel.suffix != ".py" or not (rel.parts and rel.parts[0] in ("src",)):
        continue
    src = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    try:
        tree_mod = ast.parse(src)
    except SyntaxError:
        continue
    for node in tree_mod.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            names_def[node.name] = rel

searchable = [rel for rel in walk(ROOT) if rel.suffix in (".py", ".ipynb")]

dead = []
for name, rel in names_def.items():
    cnt = 0
    uses = []
    for other in searchable:
        if other == rel:
            continue
        for i, ln in enumerate(lines_of(other), 1):
            if name in ln and not ln.lstrip().startswith(("#", "def ", "class ")):
                cnt += 1
                uses.append(f"{other}:{i}")
    if cnt == 0:  # ни одного использования вне файла определения
        dead.append(f"{rel}: {name} (использований вне файла: 0) — CANDIDATE, не верифицировано")
for d in dead[:20]:
    findings.append(("🟢", "мёртвый код (эвристика)", f"{d} — CANDIDATE, не верифицировано", ""))


# ---------------- 2. данные ----------------
data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
info.append(f"data.json: {len(data)} записей, JSON валиден.")

ids = [d.get("id") for d in data]
dup_ids = {i for i in ids if ids.count(i) > 1}
if dup_ids:
    findings.append(("🔴", "данные", f"дубли id: {dup_ids}", "docs/data.json"))
else:
    info.append("id уникальны (81/81).")

missing_fields = {}
for req in REQUIRED:
    miss = [d.get("id") for d in data if req not in d]
    if miss:
        missing_fields[req] = miss
if missing_fields:
    findings.append(("🔴", "данные",
                     f"отсутствуют обязательные поля: "
                     f"{'; '.join(f'{k} у {len(v)}' for k, v in missing_fields.items())}",
                     "docs/data.json"))
else:
    info.append("обязательные поля: все присутствуют у всех 81.")

null_fields = {req: [d["id"] for d in data if d.get(req) is None] for req in REQUIRED if req in ("dosage", "effects", "category", "code")}
nulls_clean = {k: v for k, v in null_fields.items() if v}
if nulls_clean:
    findings.append(("🟡", "данные",
                     f"поля с null: {'; '.join(f'{k} у {len(v)}' for k, v in nulls_clean.items())}: "
                     f"{'; '.join(f'{k}={v[:6]}' for k, v in nulls_clean.items())}",
                     "docs/data.json"))

zero_price = [d["id"] for d in data if d.get("price") == 0]
if zero_price:
    findings.append(("🔴", "данные", f"price=0 БАГ: {zero_price}", "docs/data.json"))
else:
    info.append("price=0: нет (price=null ок).")

zero_sci = [d["id"] for d in data if d.get("scienceIndex") == 0]
if zero_sci:
    findings.append(("🔴", "данные", f"scienceIndex=0 БАГ: {zero_sci}", "docs/data.json"))
else:
    info.append("scienceIndex=0: нет.")

# синхрон с config
sys.path.insert(0, str(ROOT))
from src import config as cfg
conf_ids = set(cfg.SUPPLEMENTS)
data_ids = set(ids)
miss_in_cfg = sorted(data_ids - conf_ids)
miss_in_data = sorted(conf_ids - data_ids)
if miss_in_cfg or miss_in_data:
    findings.append(("🟡", "config-синхрон",
                     f"в data.json, но не в SUPPLEMENTS: {miss_in_cfg}; в SUPPLEMENTS, но не в data.json: {miss_in_data}",
                     "src/config.py"))
else:
    info.append("config синхрон: SUPPLEMENTS == id data.json.")

# value = scienceIndex / (price/100)
anom = []
for d in data:
    p = d.get("price")
    s = d.get("scienceIndex")
    if p is None or p <= 0 or s is None:
        continue
    v = s / (p / 100.0)
    if v > 1000 or v < 1:
        anom.append(f"{d['id']}: sci={s} price={p} → value={v:.1f}")
if anom:
    findings.append(("🟡", "данные", f"value=scienceIndex/(price/100) аномалии (>1000 или <1): {len(anom)}", "; ".join(anom[:8])))

# эвристика вердиктов → СПИСОК НА РУЧНУЮ ПРОВЕРКУ (не баги)
CHECK = []
for d in data:
    s = d.get("scienceIndex") or 0
    v = d.get("verdict")
    if v == "работает" and s < 50:
        CHECK.append(f"{d['id']}: вердикт=работает, scienceIndex={s}")
    if v == "не подтверждено" and s > 150:
        CHECK.append(f"{d['id']}: вердикт=не подтверждено, scienceIndex={s}")
    if v == "зависит от контекста" and s > 300:
        CHECK.append(f"{d['id']}: вердикт=зависит от контекста, scienceIndex={s}")
manual = "\n".join(f"- {c}" for c in CHECK) if CHECK else "- (нет)"

# ---------- сборка отчёта ----------
red = sum(1 for f in findings if f[0] == "🔴")
yel = sum(1 for f in findings if f[0] == "🟡")
gre = sum(1 for f in findings if f[0] == "🟢")
top5 = sorted(findings, key=lambda f: {"🔴": 0, "🟡": 1, "🟢": 2}[f[0]])[:5]

sections = [
    f"# AUDIT A (S1) — карта проекта + данные",
    f"Дата: {date.today().isoformat()} | скрипт: scripts/audit_data.py | файлы НЕ менялись",
    "",
    "## Шапка",
    "| Severity | Кол-во |",
    "| --- | --- |",
    f"| 🔴 | {red} |",
    f"| 🟡 | {yel} |",
    f"| 🟢 | {gre} |",
    "",
    "## Топ-5",
    *[f"- {s} **{c}**: {m}  `{r}`" for s, c, m, r in top5],
    "",
    "## Инфо-строки",
    *[f"- {i}" for i in info],
    "",
    "## 1. Кто генерирует data.json",
] + ([f"- {h}" for h in gen_hits] if gen_hits else ["- (нет прямых write-мест)"]) + [
    "",
    "## 2. Мёртвый код (эвристика, кандидаты на ручную проверку)",
] + ([f"- {d}" for d in dead[:20]] if dead else ["- (нет)"]) + [
    "",
    "## 3. Находки (≤25)",
] + [f"{s} {c}: {m}  `{r}`" for s, c, m, r in findings[:25]] + [
    "",
    "## 4. Эвристика вердиктов — СПИСОК НА РУЧНУЮ ПРОВЕРКУ (не баги)",
    manual,
    "",
    "## 5. Дерево проекта (без .git/__pycache__/.pytest_cache/node_modules)",
    "```",
    tree,
    "```",
    "",
]
ART.parent.mkdir(parents=True, exist_ok=True)
ART.write_text("\n".join(sections), encoding="utf-8")
print(f"audit: {ART}")
print("counts:", {"🔴": red, "🟡": yel, "🟢": gre})
print("top5:")
for s, c, m, r in top5:
    print(f"  {s} {c}: {m}")