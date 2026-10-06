"""Часть E: побайтовая сверка сгенерированных страниц с эталонными.

Показывает не только число отличий, но и КАЖДУЮ отличающуюся строку с
номером — иначе «одно отличие» приходится принимать на веру.

Запуск:
    python scripts/verify_sup_diff.py <каталог_с_результатом>
"""
import hashlib
import sys
from pathlib import Path

SLUGS = ["kreatin", "omega-3", "vitamin-d", "magniy", "paba"]
ORIG = Path("docs/sup")
BOM = bytes([0xEF, 0xBB, 0xBF])


def main() -> int:
    gen = Path(sys.argv[1] if len(sys.argv) > 1
               else "docs/sup")
    print("=" * 90)
    print(f"ЧАСТЬ E: СВЕРКА {gen}")
    print("=" * 90)

    total_diff_lines = 0
    identical = 0

    for sl in SLUGS:
        a = ORIG / f"{sl}.html"
        b = gen / f"{sl}.html"
        if not b.is_file():
            print(f"\n  {sl}: НЕТ СГЕНЕРИРОВАННОГО ФАЙЛА")
            total_diff_lines += 1
            continue

        ab, bb = a.read_bytes(), b.read_bytes()
        al = ab.decode("utf-8").split("\n")
        bl = bb.decode("utf-8").split("\n")

        print(f"\n  --- {sl}.html ---")
        print(f"      байт: {len(ab):,} -> {len(bb):,} "
              f"({'+' if len(bb) > len(ab) else ''}{len(bb) - len(ab)})")
        print(f"      sha: {hashlib.sha256(ab).hexdigest()[:12]} -> "
              f"{hashlib.sha256(bb).hexdigest()[:12]}")
        print(f"      BOM: было {ab[:3] == BOM}, стало {bb[:3] == BOM}")
        print(f"      CRLF: было {ab.count(bytes([13, 10]))}, "
              f"стало {bb.count(bytes([13, 10]))}")
        print(f"      завершающий перевод строки: "
              f"было {ab.endswith(bytes([10]))}, стало {bb.endswith(bytes([10]))}")

        if ab == bb:
            print("      ФАЙЛЫ ИДЕНТИЧНЫ БАЙТ-В-БАЙТ")
            identical += 1
            continue

        n = 0
        for i in range(max(len(al), len(bl))):
            x = al[i] if i < len(al) else "<нет строки>"
            y = bl[i] if i < len(bl) else "<нет строки>"
            if x != y:
                n += 1
                total_diff_lines += 1
                print(f"      строка {i + 1}:")
                print(f"        было : {x!r}")
                print(f"        стало: {y!r}")
        print(f"      отличающихся строк: {n}")

    print()
    print("=" * 90)
    print(f"ИТОГ: идентичных файлов {identical} из {len(SLUGS)}, "
          f"отличающихся строк всего {total_diff_lines}")
    print("=" * 90)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())