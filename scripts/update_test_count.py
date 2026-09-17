"""Считает число тестов и обновляет version.json.

Использование:
    python scripts/update_test_count.py           # показать
    python scripts/update_test_count.py --apply   # записать
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = ROOT / "docs" / "version.json"


def count_tests() -> int:
    """pytest --collect-only -q даёт точное число после прогона."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-m", "not network", "--no-header"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode not in (0, 5):  # 5 = no tests collected
        print("[!] pytest вернул", r.returncode)
        print(r.stdout[-500:])
        print(r.stderr[-500:])
        sys.exit(1)
    m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout)
    if not m:
        # Иногда pytest печатает просто "X tests collected"
        m = re.search(r"^(\d+)\s*$", r.stdout, re.MULTILINE)
    if not m:
        print("[!] не смог распарсить вывод pytest:")
        print(r.stdout[-500:])
        sys.exit(1)
    return int(m.group(1))


def main() -> int:
    n = count_tests()
    d = json.loads(VERSION.read_text(encoding="utf-8"))
    old = d.get("tests")
    print(f"Сейчас в tests/: {n}")
    print(f"В version.json:  {old}")
    if n == old:
        print("[skip] совпадает, ничего не меняем")
        return 0
    if "--apply" not in sys.argv:
        print("[dry-run] --apply для записи")
        return 0
    d["tests"] = n
    VERSION.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] version.json: tests {old} -> {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
