"""Pipeline: обновление data.json за одну команду.

Шаги:
  1. fetch_metrics.py --all --apply     (wiki/citations/ongoing)
  2. recalc_science_index.py --apply    (scienceIndex, metaCount, rct)
  3. fetch_hedges_g.py --apply          (Hedges' g)
  4. enrich_dois.py --apply             (DOI в key_sources)
  5. Обновление snapshot + pytest

НЕ коммитит — владелец проверяет и коммитит вручную.

Использование:
    python scripts/update_all.py                    # все шаги
    python scripts/update_all.py --skip hedges_g    # пропустить шаг
    python scripts/update_all.py --dry-run          # без записи в data.json
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

# Каждый шаг: (имя, скрипт, аргументы для apply, аргументы для dry-run, оценка времени мин)
# (имя, скрипт, args_apply, args_dry_run, оценка_мин)
# Конвенция: у большинства скриптов "no flag" = dry-run, --apply = запись.
# У fetch_metrics.py свой флаг --dry-run/--apply.
STEPS = [
    ("metrics",   "fetch_metrics.py",        ["--all", "--apply"], ["--all", "--dry-run"], 8),
    ("science",   "recalc_science_index.py", ["--apply"],          [],                      5),
    ("hedges_g",  "fetch_hedges_g.py",       ["--apply"],          [],                     20),
    ("dois",      "enrich_dois.py",          ["--apply"],          [],                      3),
]


def run_step(name: str, script: str, args: list[str], log) -> tuple[bool, float]:
    import os
    script_path = ROOT / "scripts" / script
    if not script_path.exists():
        msg = f"[SKIP] {name}: не найден {script_path}"
        print(msg)
        log.append(msg)
        return True, 0.0

    cmd = [sys.executable, str(script_path)] + args
    print(f"\n{'=' * 70}")
    print(f"  [{name}] {' '.join(cmd[1:])}")
    print(f"{'=' * 70}")

    # Windows: принудительно UTF-8 для stdout/stderr дочернего процесса
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env,
            timeout=1800,
        )
        elapsed = time.time() - t0

        out = (result.stdout or "")[-3000:]
        err = (result.stderr or "")[-2000:]
        print(out)
        if err:
            print("[stderr]", err, file=sys.stderr)

        log.append(f"\n=== {name} ({elapsed:.0f}s, exit={result.returncode}) ===")
        log.append(out)

        if result.returncode != 0:
            return False, elapsed
        return True, elapsed
    except subprocess.TimeoutExpired:
        msg = f"[TIMEOUT] {name}: > 30 мин"
        print(msg)
        log.append(msg)
        return False, time.time() - t0
    except Exception as e:
        msg = f"[ERROR] {name}: {type(e).__name__}: {e}"
        print(msg)
        log.append(msg)
        return False, time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline обновления data.json")
    ap.add_argument("--skip", action="append", default=[],
                    help="пропустить шаг (можно несколько раз)")
    ap.add_argument("--only", action="append", default=[],
                    help="только эти шаги (можно несколько раз)")
    ap.add_argument("--apply", action="store_true",
                    help="записать изменения (по умолчанию — dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="алиас для default (для явности)")
    args = ap.parse_args()

    # Конвенция как у recalc/fetch_hedges/enrich: no flag = dry-run, --apply = запись
    is_dry = not args.apply
    if args.dry_run and args.apply:
        print("[!] --dry-run и --apply взаимоисключающие", file=sys.stderr)
        return 2

    log = [f"update_all.py — {datetime.now(timezone.utc).isoformat()}",
           f"mode: {'DRY-RUN' if is_dry else 'APPLY'}",
           f"skip: {args.skip}  only: {args.only}"]

    steps = STEPS
    if args.only:
        steps = [s for s in steps if s[0] in args.only]
    if args.skip:
        steps = [s for s in steps if s[0] not in args.skip]

    if not steps:
        print("[!] Нет шагов для выполнения")
        return 1

    total_est = sum(s[4] for s in steps)
    print(f"[Pipeline] {len(steps)} шагов, оценка времени ~{total_est} мин")
    if is_dry:
        print("[Pipeline] DRY-RUN — data.json не будет изменён (для записи: --apply)")

    t_all = time.time()
    ok_steps = []
    fail_steps = []

    for name, script, apply_args, dry_args, _ in steps:
        step_args = dry_args if is_dry else apply_args
        ok, elapsed = run_step(name, script, step_args, log)
        if ok:
            ok_steps.append((name, elapsed))
        else:
            fail_steps.append((name, elapsed))
            print(f"\n[!] Шаг {name} упал — останавливаюсь")
            break

    print(f"\n{'=' * 70}")
    print(f"  ИТОГ: {len(ok_steps)} ok, {len(fail_steps)} fail, {time.time() - t_all:.0f}s")
    print(f"{'=' * 70}")
    for name, t in ok_steps:
        print(f"  ✅ {name:12s} {t:.0f}s")
    for name, t in fail_steps:
        print(f"  ❌ {name:12s} {t:.0f}s")

    # Лог
    REPORTS.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = REPORTS / f"update_all_{ts}.log"
    log_path.write_text("\n".join(log), encoding="utf-8")
    print(f"\n[OK] Лог: {log_path}")

    if fail_steps:
        return 1

    print("\nДалее (вручную):")
    print("  $env:UPDATE_SNAPSHOT='1'; python -m pytest tests/test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT")
    print("  python -m pytest -q")
    print("  git add docs/data.json docs/data_pubmed_terms.json tests/snapshot_data.json")
    print("  git commit -m 'chore(metrics): обновление данных'")

    return 0


if __name__ == "__main__":
    sys.exit(main())