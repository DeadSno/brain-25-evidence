"""Проверка, что снапшоты действительно выполнились, а не молча пропустились.

Зачем
-----
tests/test_visual_snapshots.py берёт playwright, numpy и Pillow через
`pytest.importorskip`. Если хоть одного пакета нет, все 74 теста помечаются
SKIPPED, pytest возвращает код 0, и CI рисует зелёную галочку, не проверив ни
одного пикселя. Это худший вид «прошло»: выглядит как защита, а защиты нет.

Скрипт читает junit-xml от прогона и требует:
  * выполнено ровно EXPECTED_TESTS тестов (37 снимков × 2 движка);
  * нет failures и errors — этим владеет сам pytest, мы дублируем только
    факт ПРОГОНА, а не вердикт по пикселям;
  * пропущено не больше ALLOWED_SKIPS — сейчас это один известный пропуск
    webkit/index-412: страница 37402px выше потолка Playwright для WebKit
    (32767px), снимок в этом движке технически невозможен.

Запуск
------
    $env:RUN_SNAPSHOTS="1"
    python -m pytest -q -m snapshots --junitxml=snapshots.xml
    python scripts/check_snapshot_run.py snapshots.xml
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

# 37 снимков (18 страниц × 2 разрешения + модалка) на движок × 2 движка.
EXPECTED_TESTS = 74
ALLOWED_SKIPS = 1
ALLOWED_SKIP_NAMES = {"test_page_snapshot[webkit-412-852-index]"}


def main(path: str) -> int:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        print(f"НЕ ЧИТАЕТСЯ {path}: {exc}", file=sys.stderr)
        return 2

    # <testsuites> может обернуть один <testsuite> или содержать их сам.
    suites = ([root] if root.tag == "testsuite"
              else list(root.iter("testsuite")))
    tests = failures = errors = skipped = 0
    skip_names: list[str] = []
    for s in suites:
        tests += int(s.get("tests", 0))
        failures += int(s.get("failures", 0))
        errors += int(s.get("errors", 0))
        skipped += int(s.get("skipped", 0))
    for tc in root.iter("testcase"):
        if tc.find("skipped") is not None:
            skip_names.append(tc.get("name", "?"))

    print(f"из {path}: выполнено {tests}, пропущено {skipped}, "
          f"упало {failures + errors}")
    if skip_names:
        print("  пропущены: " + ", ".join(sorted(skip_names)))

    bad = []
    if tests != EXPECTED_TESTS:
        bad.append(
            f"выполнено {tests} тестов вместо {EXPECTED_TESTS}. Почти наверняка "
            f"playwright или Pillow не установлены: importorskip молча "
            f"помечает такие тесты пропущенными, и pytest завершается с кодом 0."
        )
    if skipped > ALLOWED_SKIPS:
        bad.append(f"пропущено {skipped} при допустимых {ALLOWED_SKIPS}.")
    unknown = sorted(set(skip_names) - ALLOWED_SKIP_NAMES)
    if unknown:
        bad.append(
            "неожиданные пропуски: " + ", ".join(unknown) + ". Если это "
            "webkit/index-412 — так и должно быть (потолок снимка 32767px)."
        )

    if bad:
        print()
        print("ПРОВЕРКА НЕ ПРОЙДЕНА:", file=sys.stderr)
        for b in bad:
            print("  - " + b, file=sys.stderr)
        return 1

    print("OK: снапшоты выполнены полностью, движок и зависимости на месте.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "snapshots.xml"))