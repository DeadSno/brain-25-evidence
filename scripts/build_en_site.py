"""Генерация физических EN-страниц в docs/en/ (SEO-01, этап 1, FIX-57).

Читает docs/*.html и docs/sup/*.html, создаёт их копии в docs/en/ и
docs/en/sup/ с adaptations для английской версии:

* lang="ru"  ->  lang="en"
* Relative пути к ресурсам получают префикс "../" (корень) или
  "../../" (sup), т.к. файлы теперь на уровень глубже.
* В <head> добавляется <meta name="lang" content="en">.
* Текст в data-i18n-text / data-i18n-* заменяется на английский из
  словаря docs/i18n.js (блок I18N.en).
* i18n.js на EN-страницах отключается через meta[name="lang"] (см.
  правку в самом i18n.js).
* В <head> добавляются canonical (на EN-URL) и 3 hreflang-тега
  (ru / en / x-default) для связки языков (SEO-01, этап 2, FIX-58).
"""

import json
import os
import re
import shutil
import glob

DOCS = "docs"
EN_DIR = os.path.join(DOCS, "en")
EN_SUP_DIR = os.path.join(EN_DIR, "sup")
I18N_PATH = os.path.join(DOCS, "i18n.js")

BASE = "https://deadsno.github.io/brain-25-evidence"


def extract_ru_dict(i18n_path):
    """Извлечь I18N.ru из i18n.js как Python-словарь (аналогично extract_en_dict)."""
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r'\bru\s*:\s*\{', content)
    if not m:
        raise ValueError("I18N.ru block not found in i18n.js")

    start = m.end() - 1
    depth = 0
    in_str = False
    str_char = None
    i = start
    end = None
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == str_char:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1

    if end is None:
        raise ValueError("could not find closing '}' of I18N.ru block")

    block = content[start:end + 1]
    pair_re = re.compile(
        r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"'
    )
    result = {}
    for k_raw, v_raw in pair_re.findall(block):
        key = json.loads('"' + k_raw + '"')
        val = json.loads('"' + v_raw + '"')
        result[key] = val

    return result


def extract_en_dict(i18n_path):
    """Извлечь I18N.en из i18n.js как Python-словарь.

    Парсит блок `en: { ... }` через поиск пар "key": "value" с учётом
    экранирования кавычек — надёжнее json.loads, т.к. внутри блока могут
    быть комментарии // и значения с //
    """
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Найти блок "en: {"
    m = re.search(r'\ben\s*:\s*\{', content)
    if not m:
        raise ValueError("I18N.en block not found in i18n.js")

    start = m.end() - 1  # позиция '{' блока en

    # Подсчёт вложенных скобок с учётом строковых литералов
    depth = 0
    in_str = False
    str_char = None
    i = start
    end = None
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == str_char:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1

    if end is None:
        raise ValueError("could not find closing '}' of I18N.en block")

    block = content[start:end + 1]

    # Извлечь все пары "key": "value" (ключ и значение в двойных кавычках,
    # с поддержкой экранированных кавычек внутри строк)
    pair_re = re.compile(
        r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"'
    )
    result = {}
    for k_raw, v_raw in pair_re.findall(block):
        # Декодировать JS-строки (\n, \uXXXX, \\ и т.д.) через JSON
        key = json.loads('"' + k_raw + '"')
        val = json.loads('"' + v_raw + '"')
        result[key] = val

    return result


def build_ru_to_en_map(ru_dict, en_dict):
    """Словарь: значение RU -> значение EN для ключей, есть в обоих словарях."""
    mapping = {}
    for key, ru_val in ru_dict.items():
        en_val = en_dict.get(key)
        if en_val is not None and en_val != ru_val:
            mapping[ru_val] = en_val
    return mapping


def translate_head_tags(html, ru_to_en):
    """Перевести <title>, meta description, og:title, og:description по ru->en map."""
    # <title>
    m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if m:
        ru_title = m.group(1).strip()
        en_title = ru_to_en.get(ru_title)
        if en_title:
            html = html.replace(f'<title>{ru_title}</title>', f'<title>{en_title}</title>', 1)

    # meta name="description"
    m = re.search(r'<meta name="description" content="(.*?)"/>', html)
    if m:
        ru_desc = m.group(1)
        en_desc = ru_to_en.get(ru_desc)
        if en_desc:
            html = html.replace(
                f'<meta name="description" content="{ru_desc}"/>',
                f'<meta name="description" content="{en_desc}"/>',
                1
            )

    # og:title
    m = re.search(r'<meta property="og:title" content="(.*?)"/>', html)
    if m:
        ru_og = m.group(1)
        en_og = ru_to_en.get(ru_og)
        if en_og:
            html = html.replace(
                f'<meta property="og:title" content="{ru_og}"/>',
                f'<meta property="og:title" content="{en_og}"/>',
                1
            )

    # og:description
    m = re.search(r'<meta property="og:description" content="(.*?)"/>', html)
    if m:
        ru_ogd = m.group(1)
        en_ogd = ru_to_en.get(ru_ogd)
        if en_ogd:
            html = html.replace(
                f'<meta property="og:description" content="{ru_ogd}"/>',
                f'<meta property="og:description" content="{en_ogd}"/>',
                1
            )

    return html


def fix_og_locale(html):
    """Заменить og:locale ru_RU -> en_US на EN-страницах."""
    return re.sub(
        r'(<meta property="og:locale" content=")ru_RU(">)',
        r'\1en_US\2',
        html
    )
    """Извлечь I18N.en из i18n.js как Python-словарь.

    Парсит блок `en: { ... }` через поиск пар "key": "value" с учётом
    экранирования кавычек — надёжнее json.loads, т.к. внутри блока могут
    быть комментарии // и значения с //
    """
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Найти блок "en: {"
    m = re.search(r'\ben\s*:\s*\{', content)
    if not m:
        raise ValueError("I18N.en block not found in i18n.js")

    start = m.end() - 1  # позиция '{' блока en

    # Подсчёт вложенных скобок с учётом строковых литералов
    depth = 0
    in_str = False
    str_char = None
    i = start
    end = None
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == str_char:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1

    if end is None:
        raise ValueError("could not find closing '}' of I18N.en block")

    block = content[start:end + 1]

    # Извлечь все пары "key": "value" (ключ и значение в двойных кавычках,
    # с поддержкой экранированных кавычек внутри строк)
    pair_re = re.compile(
        r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"'
    )
    result = {}
    for k_raw, v_raw in pair_re.findall(block):
        # Декодировать JS-строки (\n, \uXXXX, \\ и т.д.) через JSON
        key = json.loads('"' + k_raw + '"')
        val = json.loads('"' + v_raw + '"')
        result[key] = val

    return result


def fix_resource_paths(html, depth):
    """Добавить prefix к относительным путям в src/href.

    depth = 1 для docs/en/ (один уровень вверх до docs/),
    depth = 2 для docs/en/sup/ (два уровня вверх до docs/).

    Абсолютные URL (http/https), якоря (#), data:, mailto:, javascript:
    не трогаем. Если путь уже начинается с '../', число уровней
    заменяется на depth (а не прибавляется).
    """
    prefix = "../" * depth

    def repl(m):
        attr = m.group(1)
        quote = m.group(2)
        val = m.group(3)
        if re.match(r"^https?://|^#|^data:|^mailto:|^javascript:", val):
            return m.group(0)
        # Уже имеющиеся '../' заменяем на нужное количество уровней
        while val.startswith("../"):
            val = val[3:]
        return f'{attr}={quote}{prefix}{val}{quote}'

    return re.sub(r'(src|href)=(["\'])([^"\']*)\2', repl, html)


def translate_attr_value(html, attr, en_dict):
    """Заменить значение атрибута data-i18n-* на перевод."""
    pattern = re.compile(rf'{re.escape(attr)}=(["\'])([^"\']*)\1')

    def repl(m):
        quote = m.group(1)
        key = m.group(2)
        val = en_dict.get(key)
        if val is not None:
            return f'{attr}={quote}{val}{quote}'
        return m.group(0)

    return pattern.sub(repl, html)


def translate_text_content(html, en_dict):
    """Заменить текст внутри элементов с data-i18n-text="key"."""
    pattern = re.compile(
        r'(<[^>]+\bdata-i18n-text=["\']([^"\']+)["\'][^>]*>)(.*?)(</[^>]+>)',
        re.DOTALL,
    )

    def repl(m):
        tag_open = m.group(1)
        key = m.group(2)
        inner = m.group(3)
        tag_close = m.group(4)
        val = en_dict.get(key)
        if val is not None and inner.strip():
            return f'{tag_open}{val}{tag_close}'
        return m.group(0)

    return pattern.sub(repl, html)


def add_lang_meta(html):
    """Добавить <meta name="lang" content="en"> сразу после <head>."""
    if 'name="lang"' in html:
        return html
    return html.replace("<head>", '<head>\n  <meta name="lang" content="en">', 1)


def strip_i18n_markers(html):
    """Удаляет data-i18n-* маркеры из EN-страниц.

    Перевод уже применён статически, JS-переводчик отключён через
    meta[name="lang"], поэтому маркеры только мешают тестам (они ищут
    ключи в словаре, а там уже английские значения, а не ключи).
    """
    for marker in (
        "data-i18n-text",
        "data-i18n-title",
        "data-i18n-aria-label",
        "data-i18n-placeholder",
        "data-i18n-alt",
        "data-i18n-tooltip",
    ):
        html = re.sub(r'\s+' + re.escape(marker) + r'="[^"]*"', '', html)
    return html


def page_urls(rel_to_docs):
    """Вернуть (ru_url, en_url) для страницы по пути относительно docs/.

    Главная: docs/index.html -> ru https://.../ , en https://.../en/
    Карточка: docs/sup/alanin.html -> ru https://.../sup/alanin.html,
    en https://.../en/sup/alanin.html
    """
    if rel_to_docs == "index.html":
        return BASE + "/", BASE + "/en/"
    return BASE + "/" + rel_to_docs, BASE + "/en/" + rel_to_docs


def ru_en_urls_for_en(en_rel_to_docs):
    """Для EN-страницы (путь относительно docs/, начинается с 'en/'):
    вернуть (ru_url, en_url).

    en/index.html -> ru https://.../ , en https://.../en/
    en/sup/alanin.html -> ru https://.../sup/alanin.html,
    en https://.../en/sup/alanin.html
    """
    if en_rel_to_docs == "en/index.html":
        return BASE + "/", BASE + "/en/"
    ru_rel = en_rel_to_docs[len("en/"):]
    return BASE + "/" + ru_rel, BASE + "/" + en_rel_to_docs


def add_hreflang_and_canonical(html, ru_url, en_url):
    """Вставить canonical (на EN-URL) и 3 hreflang-тега в <head>.

    Абсолютные URL с доменом https://deadsno.github.io/brain-25-evidence/
    (требование SEO-01 для корректной связки языков поисковиками).
    """
    # Удалить существующий canonical и hreflang (чтобы не дублировать
    # при повторном прогоне генератора)
    html = re.sub(
        r'\s*<link rel="canonical" href="[^"]*"\s*/?>', '', html, count=1
    )
    html = re.sub(
        r'\s*<link rel="alternate" hreflang="(ru|en|x-default)"[^>]*>',
        '', html,
    )
    block = (
        f'\n  <link rel="canonical" href="{en_url}">'
        f'\n  <link rel="alternate" hreflang="ru" href="{ru_url}" />'
        f'\n  <link rel="alternate" hreflang="en" href="{en_url}" />'
        f'\n  <link rel="alternate" hreflang="x-default" href="{ru_url}" />'
    )
    # Вставить после <meta charset="utf-8"> (чтобы charset шёл перед
    # любыми link/скриптами — требование test_charset_declaration_precedes_any_fetchable_element),
    # иначе — сразу после <head>.
    if '<meta charset="utf-8">' in html:
        html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + block, 1)
    else:
        html = html.replace("<head>", "<head>" + block, 1)
    return html


def process_html(src_path, dst_path, en_dict, ru_to_en, depth):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. lang="ru" -> lang="en"
    html = html.replace('<html lang="ru"', '<html lang="en"')

    # 2. Пути к ресурсам
    html = fix_resource_paths(html, depth)

    # 3. meta lang
    html = add_lang_meta(html)

    # 4. Перевод data-i18n-text (содержимое элемента) — применяем статически
    html = translate_text_content(html, en_dict)

    # 5. Перевод data-i18n-placeholder (значение атрибута) — применяем статически
    html = translate_attr_value(html, "data-i18n-placeholder", en_dict)

    # 6. SEO-02: перевести <title>, description, og:title, og:description по ru->en map
    html = translate_head_tags(html, ru_to_en)

    # 7. SEO-03: og:locale ru_RU -> en_US
    html = fix_og_locale(html)

    # 8. Удаляем все data-i18n-* маркеры (перевод уже применён статически)
    html = strip_i18n_markers(html)

    # 9. Hreflang + canonical (EN-страница)
    rel_to_docs = os.path.relpath(dst_path, DOCS).replace("\\", "/")
    ru_url, en_url = ru_en_urls_for_en(rel_to_docs)
    html = add_hreflang_and_canonical(html, ru_url, en_url)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    en_dict = extract_en_dict(I18N_PATH)
    ru_dict = extract_ru_dict(I18N_PATH)
    ru_to_en = build_ru_to_en_map(ru_dict, en_dict)
    print(f"Извлечено переводов EN: {len(en_dict)}, RU: {len(ru_dict)}, ru->en map: {len(ru_to_en)}")

    os.makedirs(EN_SUP_DIR, exist_ok=True)

    # Корневые страницы docs/*.html -> docs/en/*.html (глубина 1 -> ../)
    root_htmls = glob.glob(os.path.join(DOCS, "*.html"))
    for src in sorted(root_htmls):
        name = os.path.basename(src)
        dst = os.path.join(EN_DIR, name)
        process_html(src, dst, en_dict, ru_to_en, 1)
        print(f"  {src} -> {dst}")

    # Sup-страницы docs/sup/*.html -> docs/en/sup/*.html (глубина 2 -> ../../)
    sup_htmls = glob.glob(os.path.join(DOCS, "sup", "*.html"))
    for src in sorted(sup_htmls):
        rel = os.path.relpath(src, DOCS)  # sup/alanin.html
        dst = os.path.join(EN_DIR, rel)
        process_html(src, dst, en_dict, ru_to_en, 2)
        print(f"  {src} -> {dst}")

    total = len(root_htmls) + len(sup_htmls)
    print(f"\nВсего EN-страниц создано: {total}")


if __name__ == "__main__":
    main()
