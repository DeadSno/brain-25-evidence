"""Watchdog битых ссылок: data.json + README. 429 от WB ≠ бита."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0"}
dead, urls = [], set()
for f in [ROOT / "docs" / "data.json", ROOT / "README.md"]:
    urls |= set(re.findall(r"https?://[^\s\"')]+", f.read_text(encoding="utf-8")))
from urllib.parse import urlparse
LOCAL_WHITELIST = {"localhost", "127.0.0.1", "0.0.0.0"}
skipped = []
for u in sorted(urls):
    parsed = urlparse(u)
    if parsed.hostname in LOCAL_WHITELIST:
        skipped.append(u)
        continue
    try:
        r = requests.head(u, headers=UA, timeout=15, allow_redirects=True)
        if r.status_code in (405, 403, 429):
            r = requests.get(u, headers=UA, timeout=15, stream=True)
        if r.status_code >= 400:
            dead.append((u, r.status_code))
    except requests.RequestException as e:
        dead.append((u, type(e).__name__))
print(f"проверено={len(urls)} битых={len(dead)} пропущено={len(skipped)}")
for u, code in dead:
    print("DEAD", code, u)
for u in skipped:
    print("SKIP (localhost)", u)
sys.exit(1 if dead else 0)
