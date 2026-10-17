"""Считает число тестов и обновляет version.json.

Использование:
    python scripts/sync_test_count.py           # показать
    python scripts/sync_test_count.py --apply   # записать

Почему команда повторяет `tests/test_version_json_counts_match_reality.py`
дословно. Число в version.json проверяет гейт, который сам зовёт
`pytest --collect-only -q` без фильтра маркеров и берёт число из строки
итога. Если здесь поставить другой набор маркеров (стоял `-m "not
network"`), счётчик посчитает не то множество тестов, что проверит
гейт, и правка version.json станет бесполезной: гейт продолжит падать.
Две реализации одного числа должны отличаться нулём бит.
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = ROOT / "docs" / "version.json"


def count_tests() -> int:
    """Число собранных тестов — тем же способом, каким его считает гейт."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if r.returncode not in (0, 5):  # 5 = no tests collected
        print("[!] pytest вернул", r.returncode)
        print(r.stdout[-500:])
        print(r.stderr[-500:])
        sys.exit(1)

    out = r.stdout or ""
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    tail = lines[-1] if lines else ""

    # Основной путь: pytest печатает итог «1157 tests collected».
    # Именно эту строку разбирает гейт, значит и мы обязаны брать её же.
    m = re.search(r"(\d+)\s+tests?\s+collected", tail) or \
        re.search(r"(\d+)\s+tests?\s+collected", out)
    if m:
        return int(m.group(1))

    # Запасной путь для старых pytest: строка на каждый node-id.
    per_node = sum(1 for l in lines if l.startswith("tests/") and "::" in l)
    if per_node:
        return per_node

    # Древний формат pytest 7: «tests/test_foo.py: 12» одной строкой на файл.
    total = 0
    for line in lines:
        m2 = re.match(r"^tests/\S+\.py:\s*(\d+)$", line)
        if m2:
            total += int(m2.group(1))
    if total:
        return total

    print("[!] не смог распарсить вывод pytest (0 тестов):")
    print(out[-800:])
    sys.exit(1)


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
    # write_bytes, а не write_text: text-режим на Windows дописывает CRLF,
    # и каждый запуск потом шатает файл, хотя содержимое не менялось.
    VERSION.write_bytes((json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"[ok] version.json: tests {old} -> {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())