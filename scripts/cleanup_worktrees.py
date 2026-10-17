#!/usr/bin/env python3
"""Удаление worktree с 0 незаякоренных коммитов относительно базовой ветки.

Использование:
    python scripts/cleanup_worktrees.py [--base v5.6.5-dev]

Запускать из главного чекаута репозитория.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Worktree:
    path: str
    head: str | None
    branch: str | None


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def list_worktrees() -> list[Worktree]:
    """Парсит `git worktree list --porcelain`."""
    proc = run(["git", "worktree", "list", "--porcelain"])
    if proc.returncode != 0:
        print(f"ОШИБКА: git worktree list --porcelain упал:\n{proc.stderr}")
        sys.exit(1)

    trees: list[Worktree] = []
    current: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line:
            if current.get("worktree"):
                trees.append(
                    Worktree(
                        path=current["worktree"],
                        head=current.get("HEAD"),
                        branch=None,
                    )
                )
                if current.get("branch"):
                    trees[-1].branch = current["branch"]
            current = {}
            continue
        if line.startswith("worktree "):
            current["worktree"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            current["HEAD"] = line[len("HEAD "):]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):]
    if current.get("worktree"):
        trees.append(Worktree(path=current["worktree"], head=current.get("HEAD"), branch=current.get("branch")))
    return trees


def is_main_checkout(path: str) -> bool:
    proc = run(["git", "rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        return False
    return os.path.abspath(path) == os.path.abspath(proc.stdout.strip())


def has_unique_commits(path: str, base: str) -> bool:
    """True, если в worktree есть коммиты, которых нет в base."""
    proc = run(["git", "-C", path, "log", f"{base}..HEAD", "--oneline"])
    return proc.returncode == 0 and bool(proc.stdout.strip())


def remove_shell_dir(path: str) -> bool:
    """Удаляет пустой каталог-оболочку на диске. True — удалён/уже отсутствует."""
    if not os.path.isdir(path):
        return True
    if os.listdir(path):
        print(f"     (каталог не пуст, не удаляем: {path})")
        return False
    try:
        os.rmdir(path)
        return True
    except OSError:
        shutil.rmtree(path, ignore_errors=True)
        return not os.path.exists(path)


def remove_worktree(path: str) -> bool:
    """Удаляет работуtree и пустой каталог-оболочку. True — удалён."""
    proc = run(["git", "worktree", "remove", path])
    if proc.returncode != 0:
        # Попытка с force (если есть нескоммиченные изменения)
        proc = run(["git", "worktree", "remove", "--force", path])
        if proc.returncode != 0:
            print(f"  !!! не удалось удалить worktree {path}: {proc.stderr.strip()}")
    # Каталог-оболочка может остаться пустым на диске — удаляем его в любом случае
    return remove_shell_dir(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Удаление worktree с 0 коммитов относительно базовой ветки",
    )
    parser.add_argument(
        "--base",
        default="v5.6.5-dev",
        help="базовая ветка для сравнения (по умолчанию v5.6.5-dev)",
    )
    args = parser.parse_args()
    base = args.base

    print(f"=== cleanup_worktrees.py — база: {base} ===")
    trees = list_worktrees()
    total = len(trees)
    removed = 0
    with_commits = 0
    skipped_main = 0

    for wt in trees:
        if is_main_checkout(wt.path):
            skipped_main += 1
            print(f"[skip] {wt.path} — главный checkout, не трогаем")
            continue

        if has_unique_commits(wt.path, base):
            with_commits += 1
            head_short = (wt.head or "?")[:7]
            print(f"[keep] {wt.path} — есть коммиты над {base} (HEAD {head_short}), пропускаем")
            continue

        print(f"[rm]   {wt.path} — нет коммитов над {base}")
        if remove_worktree(wt.path):
            removed += 1

    print()
    print("=== Отчёт ===")
    print(f"всего worktree в списке: {total}")
    print(f"пропущено (главный checkout): {skipped_main}")
    print(f"удалено (0 коммитов над {base}): {removed}")
    print(f"пропущено (есть коммиты): {with_commits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
