"""Гард: все JS в docs/ должны парситься (node --check).

Вторая половина файла (v5.6.5) закрывает дыру, из-за которой целый класс
поломок проходил мимо всех проверок: инлайновые `<script>` внутри HTML
не проверял НИКТО — `test_js_syntax` ниже берёт только `docs/*.js`.

Что реально уехало в репозиторий из-за этой дыры (коммит 45e7ed2):

  docs/sup/magniy.html — на всех 131 странице раздела:

      var name = Магний;                                    // без кавычек
      var url = https://example.org/sup/magniy.html;        // без кавычек

  Первая строка — ReferenceError, вторая — SyntaxError, и она убивала
  весь инлайновый блок целиком: кнопки «Цитировать», «Прослушать» и
  «Удиви меня» на странице не работали, а тесты молчали.

  docs/compare.html — `<script src="pwa.js" defer></script>` оказался
  ВНУТРИ инлайнового блока, до закрывающего `</script>`. Браузер
  закрывал блок на этом теге, `<script src=...>` попадал в тело как
  текст (SyntaxError), а pwa.js на странице не загружался вовсе.
  Класс ловится проверкой баланса тегов ниже.

Запуск: `pytest -q tests/test_js_syntax.py` (node должен быть в PATH).
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
NODE = shutil.which("node")
JS_FILES = sorted(p.name for p in DOCS.glob("*.js"))

#: HTML-комментарии вырезаются до поиска тегов: в offline.html строка
#: «БЕЗ внешних <link> и <script>» лежит внутри комментария и иначе
#: считалась бы незакрытым тегом.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)

#: Инлайновый <script> без src. `application/ld+json` и прочие
#: не-JS типы пропускаются: их содержимое — не JavaScript.
INLINE_SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>",
                           re.S | re.I)
SKIP_TYPES = ("application/ld+json", "application/json", "text/template",
              "text/x-handlebars")

#: Порог страховки от «зелёного вхолостую»: замер 2026-10-19 — 147
#: HTML-файлов и 582 инлайновых блока. Порог вдвое ниже, чтобы сжатие
#: разметки не роняло тест, а исчезновение выборки — роняло.
MIN_FILES = 100
MIN_INLINE = 250


@pytest.mark.skipif(NODE is None, reason="node не установлен")
@pytest.mark.parametrize("js", JS_FILES)
def test_js_syntax(js):
    r = subprocess.run([NODE, "--check", str(DOCS / js)],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"{js}: SyntaxError:\n{r.stderr}"


def _inline_bodies(text: str):
    """Инлайновые script-блоки: (номер строки, тело)."""
    out = []
    for m in INLINE_SCRIPT.finditer(text):
        attrs = m.group("attrs") or ""
        if "src=" in attrs:
            continue
        if any(t in attrs for t in SKIP_TYPES):
            continue
        body = m.group("body")
        if not body.strip():
            continue
        out.append((text[:m.start()].count("\n") + 1, body))
    return out


def test_inline_scripts_in_html_parse():
    """Каждый инлайновый <script> в docs/**/*.html обязан парситься node.

    Проверяется результат разбора, а не наличие тега: `var url = https://…`
    выглядит как обычная строка разметки и проходит любой grep.
    """
    pages = sorted(DOCS.rglob("*.html"))
    assert len(pages) >= MIN_FILES, (
        f"найдено {len(pages)} HTML-файлов, ожидалось >= {MIN_FILES} — "
        f"проверка смотрит не туда"
    )

    unbalanced = []
    failures = []
    total = 0

    for page in pages:
        raw = page.read_text(encoding="utf-8", errors="replace")
        text = HTML_COMMENT.sub("", raw)

        n_open, n_close = text.count("<script"), text.count("</script>")
        if n_open != n_close:
            unbalanced.append(
                f"{page.relative_to(DOCS.parent)}: <script>={n_open}, "
                f"</script>={n_close} — блок не закрыт или закрыт дважды"
            )
            continue

        for lineno, body in _inline_bodies(text):
            total += 1
            with tempfile.NamedTemporaryFile("w", suffix=".js",
                                            delete=False,
                                            encoding="utf-8") as tmp:
                tmp.write(body)
                tmp_path = tmp.name
            r = subprocess.run([NODE, "--check", tmp_path],
                               capture_output=True, text=True)
            Path(tmp_path).unlink(missing_ok=True)
            if r.returncode != 0:
                first = (r.stderr.strip().splitlines() or [""])[0]
                failures.append(
                    f"{page.relative_to(DOCS.parent)}:{lineno}: {first}"
                )

    assert total >= MIN_INLINE, (
        f"инлайновых <script> найдено {total}, ожидалось >= {MIN_INLINE} — "
        f"детектор перестал видеть разметку"
    )
    assert not unbalanced, (
        "Незакрытые/задвоенные теги <script>:\n  " + "\n  ".join(unbalanced)
    )
    assert not failures, (
        f"Инлайновый JS не парсится (проверено {total} блоков):\n  "
        + "\n  ".join(failures)
    )
