"""One-shot диагностика для старта сессии с AI.

Вывод скинуть AI в первом сообщении.

Запуск:  python scripts/check_state.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def safe_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    # 1. Карточки
    section("КАРТОЧКИ")
    data = safe_json(ROOT / "docs" / "data.json")
    drafts = safe_json(ROOT / "docs" / "_drafts.json")
    print(f"data.json:    {len(data) if data else '—'}")
    print(f"_drafts.json: {len(drafts) if drafts else '—'}")
    if drafts:
        print("\nНезаполненные:")
        for c in drafts:
            print(f"  - {c.get('name', '?')} ({c.get('category', '?')})")

    # 2. Proposals
    section("PROPOSALS (последние 5)")
    proposals = sorted(
        (ROOT / "reports").glob("*_proposal.json"),
        key=lambda p: p.stat().st_mtime, reverse=True
    )[:5]
    for p in proposals:
        d = safe_json(p)
        print(f"  {p.name}: {len(d) if d else 0}")

    # 3. Git
    section("GIT")
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        print(log.stdout)
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        print("Незакоммичено:" if status.stdout.strip() else "[clean]")
        if status.stdout.strip():
            print(status.stdout)
    except Exception as e:
        print(f"[git error] {e}")

    # 4. Тесты — только сборка
    section("ТЕСТЫ")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q", "-m", "not network"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace"
        )
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        print(lines[-1] if lines else "—")
    except Exception as e:
        print(f"[error] {e}")

    # 5. Версия
    section("ВЕРСИЯ")
    v = safe_json(ROOT / "docs" / "version.json")
    if v:
        for k, val in v.items():
            print(f"  {k}: {val}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())