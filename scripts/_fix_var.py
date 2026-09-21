"""Замена var → let в docs/tracker.js. Безопасная механическая замена."""
from pathlib import Path
import re

TRACKER = Path("docs/tracker.js")
text = TRACKER.read_text(encoding="utf-8")
original = text

# Меняем var → let (word boundary, чтобы не трогать "vary" и т.д.)
new_text, n = re.subn(r"\bvar\s+", "let ", text)

TRACKER.write_text(new_text, encoding="utf-8")
print(f"[OK] Заменено var → let: {n} мест")
print(f"[OK] Файл: {TRACKER}")