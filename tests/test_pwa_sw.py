"""
Тесты PWA и Service Worker — FIX-72 (QA-09).

Проверяют:
  1. Все файлы из STATIC_ASSETS в docs/sw.js реально существуют в docs/.
  2. Все иконки из docs/manifest.webmanifest существуют.
  3. docs/pwa.js не содержит синтаксических ошибок (node --check).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SW_PATH = DOCS / "sw.js"
MANIFEST_PATH = DOCS / "manifest.webmanifest"
PWA_JS_PATH = DOCS / "pwa.js"


def _extract_static_assets() -> list[str]:
    """Извлечь список STATIC_ASSETS из docs/sw.js.

    Массив объявлен как `var STATIC_ASSETS = [ ... ];`. Берём содержимое
    между `[` и соответствующим `]`, затем вытаскиваем строковые литералы
    `'...'` или `"..."`.
    """
    src = SW_PATH.read_text(encoding="utf-8")
    m = re.search(r"var\s+STATIC_ASSETS\s*=\s*(\[[\s\S]*?\])\s*;", src)
    if not m:
        pytest.fail(f"STATIC_ASSETS не найден в {SW_PATH}")
    arr_text = m.group(1)
    urls = re.findall(r'["\']([^"\']+)["\']', arr_text)
    return urls


# ─────────────────────────── тесты ───────────────────────────


def test_static_assets_exist():
    """Все файлы из STATIC_ASSETS (sw.js) должны существовать в docs/."""
    assets = _extract_static_assets()
    assert assets, f"STATIC_ASSETS пуст в {SW_PATH}"
    missing = []
    for url in assets:
        # Убираем ведущий './' и query-части (?v=...) перед проверкой пути.
        rel = url.lstrip("./").split("?")[0].split("#")[0]
        # На Windows '/' в rel — это разделитель каталогов, Path справится.
        p = DOCS / rel
        if not p.exists():
            missing.append(url)
    assert not missing, (
        f"Файлы из STATIC_ASSETS не найдены в {DOCS}: {missing}"
    )


def test_manifest_icons_exist():
    """Все src иконок из manifest.webmanifest должны существовать."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    icons = manifest.get("icons", [])
    assert icons, f"В {MANIFEST_PATH} нет иконок"
    missing = []
    for icon in icons:
        src = icon.get("src", "")
        rel = src.lstrip("./")
        p = DOCS / rel
        if not p.exists():
            missing.append(src)
    assert not missing, (
        f"Иконки из {MANIFEST_PATH} не найдены в {DOCS}: {missing}"
    )


def test_pwa_js_syntax():
    """docs/pwa.js не должен содержать синтаксических ошибок."""
    if not PWA_JS_PATH.exists():
        pytest.skip(f"{PWA_JS_PATH} не найден")
    # Пытаемся node --check; если Node нет —落ちмся с skip.
    try:
        result = subprocess.run(
            ["node", "--check", str(PWA_JS_PATH)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        pytest.skip("node не найден в PATH — проверка синтаксиса пропущена")
    if result.returncode != 0:
        pytest.fail(
            f"pwa.js содержит синтаксические ошибки:\n{result.stderr}"
        )
