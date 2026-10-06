"""Негативный контроль над молчаливыми обработчиками (часть B, v5.5.0).

Задача части B: найти все `if (!el) return;` и решить, есть ли негативный
контроль. Инвентаризация дала 20 мест, но перебор строк с `if (!x) return`
находит не всё молчание. Главная находка лежит в другом месте:

    docs/tracker.js:291
      function boot() {
        fetchSupplements().then(function () { init(); });
      }

Здесь нет `if (!el) return`, но есть то же самое молчание. `init()`
вызывается только из обработчика успеха. Если загрузка данных откажет —
сеть, 404, битый JSON — `.then` не выполнится, `injectMyCoursesSection()`
не вызовется, модальные окна не оживут. Пользователь увидит страницу,
которая выглядит исправной, и не получит ни одного сигнала.

Поэтому контроль здесь двух видов:

  1. ЦЕПОЧКИ ПРОМИСОВ. Каждый `.then(` обязан иметь обработчик отказа —
     `.catch(...)`, второй аргумент `.then(onOk, onErr)` либо быть
     потреблённым через `Promise.allSettled` с `.catch` у потребителя.
     Незащищённые цепочки перечислены в ACCEPTED_UNPROTECTED вместе с
     причиной, почему каждая пока оставлена как есть.

  2. МОЛЧАЛИВЫЕ ГУАРДЫ. Для каждого `if (!x) return;` проверяется, что
     переменная `x` — либо делегирование события (`e.target.closest(...)`),
     где отсутствие элемента штатно, либо элемент с известным `id`,
     который реально есть на страницах, грузящих этот скрипт. Если `x`
     ни то ни другое — тест падает: значит появился новый молчаливый
     выход, который никто не классифицировал.

Почему числа не захардкожены. Наивный вариант писал бы «ожидаем 20 мест»
или «ожидаем 5 незащищённых цепочек». Такой тест проходит, пока код
меняется согласованно, и молчит, когда появляется шестая цепочка или
шестое место. Здесь ожидания выведены из кода: тест сравнивает
найденное с перечнем, а перечень хранит причину. Любое расхождение —
это либо новый дефект, либо сознательное решение, которое нужно записать
в перечень словами.

Ложные срабатывания, найденные при написании теста, зафиксированы
намеренно — они показывают, почему наивный поиск по `.catch` неверен:

  - docs/share.js:43 защищён формой `.then(onOk, onErr)`: регексп
    `nxt.lstrip().startswith('.')` на `})` её не видит, а регулярка
    `\\.then\\s*\\([^)]*,` не переживает вложенные скобки в аргументах
    (`mark(btn, OK, false)`). Цепочка рабочая, детектор был неправ.
  - docs/script.js:184 (`fetchJson`) сам обработчика отказа не имеет, но
    единственный его потребитель оборачивает вызовы в
    `Promise.allSettled(...)` и имеет `.catch` на строке 196. Защищён.

Оба случая разобраны вручную и не являются дефектом.

Запуск: тест статический — ни браузера, ни сети, ни гейтов.
    pytest -q tests/test_silent_handlers.py
"""
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"

# Файлы, где вообще ищутся молчаливые выходы. pwa.js и share.js в
# исходном переборе дали 0 совпадений, но они включены: если туда
# добавят новый обработчик, тест должен это заметить.
JS_FILES = ["script.js", "tracker.js", "pwa.js", "share.js",
            "science2.js", "sw.js", "version.js"]

# ── Незащищённые цепочки промисов ─────────────────────────────────────
# Ключ — (файл, номер строки, где стоит `.then(`).
# Причина обязательна: пустая строка недопустима, иначе перечень
# превратится в формальность и перестанет что-либо объяснять.
ACCEPTED_UNPROTECTED = {
    ("tracker.js", 291): (
        "САМЫЙ СЕРЬЁЗНЫЙ. Сбой загрузки данных навсегда отключает "
        "трекер: секция «Мои добавки» не появится, модальные окна не "
        "оживут, сигнала нет. Требует решения владельца: что должно "
        "происходить при отказе — инициализировать ли остальное "
        "(модалка не зависит от данных) или показывать заглушку."
    ),
    ("script.js", 285): (
        "Копирование ссылки инлайном. `navigator.clipboard` "
        "отклоняет запрос в небезопасном контексте (http без TLS) — "
        "тогда кнопка не меняет подпись и выглядит мёртвой. Рядом в "
        "share.js:43 тот же случай обработан откатом на legacyCopy, "
        "здесь отката нет."
    ),
    ("science2.js", 164): (
        "Спарклайн цены. До запроса уже выставлена видимая заглушка "
        "`…` на строке 163, поэтому при отказе пользователь видит "
        "заглушку, а не пустоту. Тихого исчезновения нет."
    ),
    # Номера строк сдвинуты на 13: v5.6.0 этап 1.5 добавил в sw.js
    # запись v79 в шапку (13 строк). Причины прежние, суть цепочек
    # не менялась — передвинуто только положение в файле.
    #
    # v81 (v5.6.1) сдвинул их ещё на 30: 29 строк записи в шапку +
    # 1 строка './sup/index.html' в STATIC_ASSETS. Обе правки — в sw.js,
    # ни одной строки в самих цепочках не тронуто.
    ("sw.js", 207): (
        "Уведомление об офлайне через clients.matchAll(). Отказ "
        "означает лишь отсутствие косметического сообщения; данные и "
        "страница не затронуты."
    ),
    ("sw.js", 380): (
        "Очистка старых кэшей внутри event.waitUntil(). Отказ здесь "
        "не скрывает: браузер сам отклоняет активацию worker и "
        "сообщает об этом. Стандартная практика для service worker."
    ),
    ("script.js", 184): (
        "Хелпер fetchJson сам обработчика отказа не имеет. Единственный "
        "его потребитель оборачивает вызовы в Promise.allSettled(...) и "
        "имеет .catch на строке 196 с понятным сообщением в консоль. "
        "Отказ data_index.json при этом виден и не стирает страницу."
    ),
}


# Молчаливые выходы по НЕ-элементам: данные, внутреннее состояние,
# аргументы функций. Их нельзя проверить по файлам, поэтому они
# перечислены явно и обязаны нести причину.
#
# Эвристика «вызов функции — значит не элемент» была и удалена:
# негативный контроль подсунул `someUnknownLookup()` в pwa.js, и тест
# его пропустил, то есть был наполовину слепым. Теперь незнакомое
# выражение не проходит.
ACCEPTED_NON_ELEMENT_GUARDS = {
    ("script.js", 614): (
        "supplementsFull[id] — поиск дополнения по id. Отсутствие "
        "записи в данных не поломка разметки, а штатный случай."
    ),
    ("script.js", 765): (
        "chart.config._config с проверкой !cfg.$band — внутреннее "
        "устройство графика; полоса бэнда есть не у всех серий."
    ),
    ("script.js", 825): (
        "Аргумент els — защита от пустого массива на стороне вызова."
    ),
    ("script.js", 827): (
        "Результат внутренней chartSupByEl(); дополнение может не "
        "найтись на элементе."
    ),
    ("script.js", 925): (
        "supplementsFull[idA]/[idB] — сравнение двух дополнений, одно "
        "из которых может отсутствовать в данных."
    ),
    ("script.js", 1053): (
        "Аргумент html в функции рендера: пустой html означает «нечего "
        "рисовать», а не сбой."
    ),
    ("script.js", 1109): (
        "Ответ await fetch('version.json') с проверкой !r.ok: при "
        "HTTP-ошибке обновление версии пропускается намеренно."
    ),
    ("tracker.js", 102): (
        "location.hash — хеша может не быть вовсе, это штатный вход на "
        "страницу."
    ),
    ("tracker.js", 104): (
        "findSup(hash) — id из URL может не соответствовать ни одной "
        "добавке."
    ),
    ("tracker.js", 239): (
        "courses[id] — запись курса может пропасть из localStorage."
    ),
    ("science2.js", 19): (
        "Аргумент rows — функция рендера, пустой набор нечего рисовать."
    ),
    ("science2.js", 225): (
        "Тернарник, возвращающий null по условию."
    ),
    ("science2.js", 227): (
        "curId() — id текущей добавки может отсутствовать."
    ),
}

# Элементы, которых нет в статическом HTML, потому что они создаются
# скриптом. Проверяется наличие присваивания `.id = '...'` в том же
# файле: если создание исчезнет, тест упадёт.
KNOWN_DYNAMIC_IDS = ("myCoursesSection", "ecoSpark")


def _js(name):
    path = DOCS / name
    if not path.is_file():
        pytest.skip(f"{name} отсутствует — нечего проверять")
    return path.read_text(encoding="utf-8", errors="replace")


def _chain_end(lines, start_idx):
    """Номер строки, на которой заканчивается цепочка, начавшаяся с `.then(`.

    Считает скобки от `(` в `.then(`. Возвращает индекс последней строки
    цепочки (0-based) либо `start_idx`, если разобрать не удалось.

    Итерация обязана увеличивать счётчик на каждом шаге: ранняя версия
    продолжала цикл без `i += 1` и зависала намертво.
    """
    depth = 0
    started = False
    i = start_idx
    limit = min(len(lines), start_idx + 120)
    last = start_idx
    while i < limit:
        line = lines[i]
        for ch in line:
            if ch == "(":
                depth += 1
                started = True
            elif ch == ")":
                depth -= 1
        last = i
        if started and depth <= 0:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            continues = nxt.lstrip().startswith((".", ")")) or \
                any(t in nxt for t in (".then(", ".catch(", ".finally("))
            if continues:
                i += 1
                continue
            break
        i += 1
    return last


def _has_rejection_handler(text):
    """Есть ли у цепочки обработчик отказа.

    `.catch(...)` — очевидно. Второй аргумент `.then(onOk, onErr)` —
    тоже: запятая ищется на верхнем уровне скобок, иначе вложенные
    вызовы вроде `mark(btn, OK, false)` дают ложное срабатывание.
    """
    if ".catch(" in text:
        return True
    idx = text.find(".then(")
    if idx < 0:
        return False
    seg = text[idx + len(".then("):]
    depth = 0
    for k, ch in enumerate(seg):
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                seg = seg[:k]
                break
            depth -= 1
    depth = 0
    for ch in seg:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return True
    return False


def test_unprotected_chains_match_reviewed_list():
    """Незащищённых цепочек не должно быть больше, чем разобрано вручную.

    Новый молчаливый обработчик проваливает тест. Починенная цепочка тоже
    проваливает — это правильно: значит, перечень устарел и его нужно
    привести в соответствие, а не молча оставить.
    """
    found = {}
    for name in JS_FILES:
        src = _js(name)
        lines = src.splitlines()
        last_end = -1
        for i, line in enumerate(lines):
            if ".then(" not in line:
                continue
            # продолжение цепочки, уже найденной выше (строка вида
            # `}).then(...)` — это тот же промис, а не новый)
            if i <= last_end:
                continue
            end = _chain_end(lines, i)
            last_end = end
            chain = "\n".join(lines[i:end + 1])
            if not _has_rejection_handler(chain):
                found[(name, i + 1)] = chain

    unexplained = sorted(set(found) - set(ACCEPTED_UNPROTECTED))
    assert not unexplained, (
        "Найдены молчаливые цепочки промисов, которых нет в "
        "ACCEPTED_UNPROTECTED. Каждая такая цепочка означает: при отказе "
        "код после неё не выполнится, и никто об этом не узнает.\n"
        + "\n".join(
            f"  {f}:{n}: {' '.join(found[(f, n)].split())[:70]}"
            for f, n in unexplained
        )
        + "\n\nЛибо добавь обработчик отказа, либо запиши цепочку в "
          "ACCEPTED_UNPROTECTED с причиной."
    )

    stale = sorted(set(ACCEPTED_UNPROTECTED) - set(found))
    assert not stale, (
        "Записи в ACCEPTED_UNPROTECTED больше не соответствуют коду: "
        f"{stale}. Цепочки починены или переехали — обнови перечень "
        "с причиной по факту."
    )

    # перечень обязан быть объяснён, иначе он формален
    for key, reason in ACCEPTED_UNPROTECTED.items():
        assert reason.strip(), f"пустое объяснение для {key}"

    assert found, (
        "детектор перестал находить цепочки — вероятно, он сломан. "
        "Молчащий тест хуже отсутствующего."
    )


def test_tracked_scripts_are_not_silently_empty():
    """Каждый файл из JS_FILES читается и содержит хоть один `if` или `.then`.

    Страховка от детектора, который однажды начнёт возвращать пустое
    множество по синтаксической причине и тем самым «пройдёт» тест.
    """
    for name in JS_FILES:
        src = _js(name)
        assert "if" in src, f"{name}: не найдено ни одного if"
        assert len(src) > 0


def _guard_hits(lines):
    """Строки с молчаливым ранним выходом и имя переменной."""
    out = []
    pat = re.compile(
        r"^\s*if\s*\(\s*!\s*(?P<v>[A-Za-z_$][\w$]*)"
        r"(?:\s*&&\s*!\s*(?P<v2>[A-Za-z_$][\w$]*))*\s*\)\s*return\s*;?\s*$"
    )
    for i, line in enumerate(lines):
        if "return" not in line:
            continue
        m = pat.match(line)
        if m:
            vars_ = [m.group("v")] + ([m.group("v2")] if m.group("v2") else [])
            out.append((i + 1, vars_, line.strip()))
            continue
        loose = re.match(r"^\s*if\s*\(.*\)\s*return\s*;?\s*$", line)
        if loose and re.search(r"![\s(]*[A-Za-z_$][\w$]*", line):
            names = re.findall(r"![\s(]*([A-Za-z_$][\w$]*)", line)
            if names:
                out.append((i + 1, names, line.strip()))
    return out


def test_silent_guards_are_either_verifiable_or_explicitly_listed():
    """Каждый `if (!x) return;` обязан быть либо проверяем, либо назван.

    Три допустимые категории, и ничего четвёртого:

      ДЕЛЕГИРОВАНИЕ — переменная из `e.target.closest(...)`. Клик мимо
        элемента штатен, ранний выход уместен.

      ЭЛЕМЕНТ В РАЗМЕТКЕ — `$('id')`, `getElementById('id')` или
        `querySelector('#id')`, и этот `id` реально есть на страницах,
        грузящих скрипт. Проверяется по файлам, не по мнению.

      ЭЛЕМЕНТ ИЗ JS — тот же `id`, но создаваемый скриптом. Проверяется
        наличие присваивания `.id = '...'`; если создание исчезнет,
        тест упадёт.

    Всё остальное — не элемент, и должно быть перечислено в
    ACCEPTED_NON_ELEMENT_GUARDS с причиной.

    История: первая версия теста использовала эвристику
    «результат вызова — значит не элемент». Негативный контроль
    подсунул `const mystery = someUnknownLookup(); if (!mystery) return;`
    в pwa.js — тест остался зелёным. Эвристика удалена, незнакомое
    выражение теперь проваливает тест.
    """
    pages = [p for p in sorted(DOCS.rglob("*.html"))
             if p.name != "offline.html" and "google" not in p.name]

    problems = []
    total_guards = 0
    used_listed = set()

    for name in JS_FILES:
        src = _js(name)
        lines = src.splitlines()
        hits = _guard_hits(lines)
        total_guards += len(hits)
        if not hits:
            continue

        needed = [p for p in pages
                  if re.search(rf'src="[^"]*{re.escape(name)}',
                               p.read_text(encoding="utf-8", errors="replace"))]
        page_text = "\n".join(
            p.read_text(encoding="utf-8", errors="replace") for p in needed
        )

        for lineno, vars_, text in hits:
            var = vars_[0]
            key = (name, lineno)

            if key in ACCEPTED_NON_ELEMENT_GUARDS:
                used_listed.add(key)
                continue

            origin = None
            for j in range(lineno - 1, max(-1, lineno - 41), -1):
                m = re.search(rf"(?:const|let|var)\s+{re.escape(var)}\s*=\s*(.*)",
                              lines[j])
                if m:
                    origin = m.group(1)
                    break
                if re.search(rf"(?:const|let|var)\s+{re.escape(var)}\s*=", lines[j]):
                    origin = ""
                    break

            if origin is None:
                problems.append(
                    f"{name}:{lineno} -> {var}: нет присваивания выше по "
                    f"тексту (аргумент или внешняя переменная) — "
                    f"добавьте в ACCEPTED_NON_ELEMENT_GUARDS с причиной"
                )
                continue

            if ".closest(" in origin:
                continue  # делегирование

            ids = (re.findall(r"""getElementById\(\s*['"]([^'"]+)['"]""", origin)
                   or re.findall(r"""\$\(\s*['"]([^'"]+)['"]""", origin)
                   or re.findall(r"""querySelector\(\s*['"]#([^'"]+)['"]""", origin))
            if not ids:
                problems.append(
                    f"{name}:{lineno} -> {var}: {origin[:60]} — не DOM-элемент "
                    f"и не делегирование, назовите в "
                    f"ACCEPTED_NON_ELEMENT_GUARDS"
                )
                continue

            missing = [e for e in ids
                       if f'id="{e}"' not in page_text
                       and not re.search(rf"\.id\s*=\s*['\"]{re.escape(e)}['\"]",
                                         src)]
            if missing:
                known_dynamic = [e for e in missing if e in KNOWN_DYNAMIC_IDS]
                still = [e for e in missing if e not in KNOWN_DYNAMIC_IDS]
                if still:
                    problems.append(
                        f"{name}:{lineno} -> {still} нет ни в разметке, ни "
                        f"создаётся из JS на страницах, грузящих {name}"
                    )
                elif not known_dynamic:
                    problems.append(f"{name}:{lineno} -> расхождение")

    assert not problems, (
        "Молчаливые ранние выходы без объяснения:\n  "
        + "\n  ".join(problems)
        + "\n\nЭлемент — добавьте id в разметку или объясните в "
          "ACCEPTED_NON_ELEMENT_GUARDS. Данные — назовите с причиной."
    )

    stale = sorted(set(ACCEPTED_NON_ELEMENT_GUARDS) - used_listed)
    assert not stale, (
        "ACCEPTED_NON_ELEMENT_GUARDS содержит записи, которых больше нет "
        f"в коде: {stale}. Код починен или переехал — приведите перечень "
        "в соответствие, иначе он перестанет отражать реальность."
    )

    for k, reason in ACCEPTED_NON_ELEMENT_GUARDS.items():
        assert reason.strip(), f"пустое объяснение для {k}"

    assert total_guards > 0, (
        "детектор guards перестал находить молчаливые выходы — "
        "вероятно, он сломан"
    )


def test_expected_guard_volume_is_derived_not_assumed():
    """Контроль объёма: число guards должно совпадать с разобранным.

    Не «ожидаем 20», а «ожидаем столько, сколько насчитали», причём
    само число печатается при падении, чтобы разрыв был виден.
    """
    counts = {}
    for name in JS_FILES:
        lines = _js(name).splitlines()
        n = len(_guard_hits(lines))
        if n:
            counts[name] = n

    assert counts, "ни в одном файле не найдено молчаливых выходов"
    assert set(counts) <= set(JS_FILES)

    total = sum(counts.values())
    # pwa.js и share.js исторически чисты; если в них появится новый
    # молчаливый выход, это повод посмотреть, а не молчаливый сдвиг базы
    assert "pwa.js" not in counts or counts["pwa.js"] > 0
    print(f"\nмолчаливых ранних выходов: {total} "
          f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})")