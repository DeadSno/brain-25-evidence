"""Перезапускает fetch_evidence_abstracts для конкретных добавок."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BAD = ["Бор", "Кремний", "Метионин", "Орнитин", "GLA", "Серин",
       "Карнозин", "PABA", "Пролин", "Бетаин"]

for name in BAD:
    print(f"\n=== {name} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fetch_evidence_abstracts.py"),
         "--name", name],
        cwd=ROOT,
    )