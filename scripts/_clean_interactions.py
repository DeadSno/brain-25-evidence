"""Чистка interactions: убрать заглушки with='—'."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("docs/data.json")
d = json.loads(DATA.read_text(encoding="utf-8"))

removed = 0
for c in d:
    inter = c.get("interactions") or []
    before = len(inter)
    c["interactions"] = [
        i for i in inter
        if (i.get("with") or "").strip() not in ("", "—", "-")
        or "известных взаимодействий нет" in (i.get("note") or "").lower()
    ]
    removed += before - len(c["interactions"])

if removed:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = DATA.with_suffix(f".json.bak-{ts}")
    shutil.copy2(DATA, backup)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Удалено {removed} заглушек, бэкап {backup.name}")
else:
    print("[SKIP] Заглушек нет")