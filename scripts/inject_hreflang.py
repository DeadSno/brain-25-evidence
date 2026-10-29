"""Инжектит canonical + 3 hreflang-тега в исходные RU-страницы docs/*.html и docs/sup/*.html.

Каждая RU-страница получает связку с парной EN-страницей:

  <link rel="canonical" href="https://deadsno.github.io/brain-25-evidence/ОТНОСИТЕЛЬНЫЙ_ПУТЬ_RU">
  <link rel="alternate" hreflang="ru" href="https://deadsno.github.io/brain-25-evidence/ОТНОСИТЕЛЬНЫЙ_ПУТЬ_RU" />
  <link rel="alternate" hreflang="en" href="https://deadsno.github.io/brain-25-evidence/en/ОТНОСИТЕЛЬНЫЙ_ПУТЬ_EN" />
  <link rel="alternate" hreflang="x-default" href="https://deadsno.github.io/brain-25-evidence/ОТНОСИТЕЛЬНЫЙ_ПУТЬ_RU" />

Запуск:

    python scripts/inject_hreflang.py
"""

import glob
import os
import re

DOCS = "docs"
BASE = "https://deadsno.github.io/brain-25-evidence"


def page_urls(rel_to_docs):
    """Вернуть (ru_url, en_url) для страницы по пути относительно docs/."""
    if rel_to_docs == "index.html":
        return BASE + "/", BASE + "/en/"
    return BASE + "/" + rel_to_docs, BASE + "/en/" + rel_to_docs


def process_html(src_path):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    rel_to_docs = os.path.relpath(src_path, DOCS).replace("\\", "/")
    ru_url, en_url = page_urls(rel_to_docs)

    # Удалить существующий canonical и hreflang (чтобы не дублировать при повторном прогоне)
    html = re.sub(
        r'\s*<link rel="canonical" href="[^"]*"\s*/?>', '', html, count=1
    )
    html = re.sub(
        r'\s*<link rel="alternate" hreflang="(ru|en|x-default)"[^>]*>',
        '', html,
    )

    block = (
        f'\n  <link rel="canonical" href="{ru_url}">'
        f'\n  <link rel="alternate" hreflang="ru" href="{ru_url}" />'
        f'\n  <link rel="alternate" hreflang="en" href="{en_url}" />'
        f'\n  <link rel="alternate" hreflang="x-default" href="{ru_url}" />'
    )
    # Вставить после <meta charset="utf-8"> (чтобы charset шёл перед
    # любыми link/скриптами), иначе — сразу после <head>.
    if '<meta charset="utf-8">' in html:
        html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + block, 1)
    else:
        html = html.replace("<head>", "<head>" + block, 1)

    with open(src_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    files = sorted(
        glob.glob(os.path.join(DOCS, "*.html"))
        + glob.glob(os.path.join(DOCS, "sup", "*.html"))
    )
    for f in files:
        process_html(f)
        print(f"  {f}")
    print(f"\nВсего RU-страниц обновлено: {len(files)}")


if __name__ == "__main__":
    main()
