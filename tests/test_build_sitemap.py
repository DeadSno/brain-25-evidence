"""Тесты scripts/build_sitemap.py — ловят два бага, найденных 2026-10-08.

Оба вылезли на CI как падение шага «Sitemap check» на коммите батча C
и ничем не ловились: генератора в тестах не было вообще.

1. Наивный pre-commit hook не работает. `git log` не видит незакоммиченные
   правки, поэтому страница, уже добавленная в индекс, получала в lastmod
   дату своего ПРЕДЫДУЩЕГО коммита. Генерация до коммита давала glossary
   2026-10-07, а CI после коммита считал 2026-10-08 → FAIL. Лечится
   `--commit-date`: файл из индекса получает дату коммита, не из индекса —
   дату из истории.

2. Самоссылка главной страницы. У главной loc пустой (её canonical — с
   косой чертой), и путь строился из loc → `docs/`, то есть «любой файл
   в docs». В это множество попадал сам sitemap.xml, поэтому КАЖДЫЙ коммит,
   чинящий sitemap, делал его снова устаревшим — и `--check` падал даже
   на коммите, где менялся только sitemap.xml.

Сеть не используется. git вызывается по-настоящему, но только на временном
клоне, созданном в tmp_path: живой репозиторий тесты не трогают.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_sitemap as bs  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="нужен git"
)


# --------------------------------------------------------------------------
# Фикстура: минимальный клон, где есть git, docs/ и генератор.
# --------------------------------------------------------------------------

#: Страницы для фикстуры берём из самого ROOT_PAGES: генератор обязан видеть
#: все 12 корневых страниц, иначе он честно падает с «Нет контентной
#: страницы» — это его штатная защита, а не баг фикстуры.


@pytest.fixture()
def repo(tmp_path):
    """Репозиторий со страницами из ROOT_PAGES и генератором из этого дерева."""
    root = tmp_path / "repo"
    (root / "docs" / "sup").mkdir(parents=True)
    for name, _freq, _prio in bs.ROOT_PAGES:
        (root / "docs" / name).write_text("<html></html>\n", encoding="utf-8")
    (root / "docs" / "sup" / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (root / "docs" / "sup" / "aaa.html").write_text("<html></html>\n", encoding="utf-8")

    scripts = root / "scripts"
    scripts.mkdir()
    shutil.copy(ROOT / "scripts" / "build_sitemap.py", scripts / "build_sitemap.py")

    def git(*args, **env):
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**_base_env(), **env},
            check=True,
        ).stdout

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    git("add", "-A")
    git("commit", "-q", "-m", "initial", **{"GIT_AUTHOR_DATE": "2026-01-01T00:00:00"})
    return root


def _base_env():
    import os

    env = dict(os.environ)
    # Детерминированные даты: тест не должен зависеть от «сегодня».
    env.pop("GIT_AUTHOR_DATE", None)
    env.pop("GIT_COMMITTER_DATE", None)
    env["TZ"] = "UTC"
    # Кодировка вывода генератора задаётся явно. Без неё дочерний Python
    # берёт кодировку консоли (на Windows это cp1251/cp866), тест же читает
    # вывод как utf-8 — и русские сообщения об ошибках превращаются в
    # «кракозябры». Замер 2026-10-08: с PYTHONIOENCODING=utf-8 в окружении
    # 10 тестов зелёные, без него падают два — те, что проверяют текст ошибок.
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_script(repo, *args):
    """Запустить генератор в клоне, вернуть (returncode, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "build_sitemap.py"), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_base_env(),
    )
    return proc.returncode, proc.stdout + proc.stderr


def git(repo, *args, date=None, check=True):
    """git в клоне. `date` фиксирует дату коммита (иначе берётся сегодня)."""
    env = _base_env()
    if date:
        env["GIT_AUTHOR_DATE"] = f"{date}T00:00:00"
        env["GIT_COMMITTER_DATE"] = f"{date}T00:00:00"
    proc = subprocess.run(
        ["git", *args],
        cwd=repo, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} упал:\n{proc.stderr}")
    return proc


def commit_all(repo, message, date):
    """Закоммитить ВСЁ, что есть в рабочем дереве, с заданной датой."""
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, date=date)


def lastmod_of(repo, loc_suffix):
    """Значение <lastmod> для URL, оканчивающегося на loc_suffix."""
    text = (repo / "docs" / "sitemap.xml").read_text(encoding="utf-8")
    blocks = text.split("<url>")
    for block in blocks:
        if f"{bs.BASE}{loc_suffix}</loc>" in block:
            for line in block.splitlines():
                if "<lastmod>" in line:
                    return line.strip().split("<lastmod>")[1].split("</lastmod>")[0]
    raise AssertionError(f"нет {loc_suffix} в sitemap")


# --------------------------------------------------------------------------
# Баг 1: файл из индекса должен получать дату коммита, а не прошлую.
# --------------------------------------------------------------------------


def test_staged_page_gets_commit_date_not_previous(repo):
    """Главный сценарий хука: страница в индексе + --commit-date."""
    rc, out = run_script(repo)
    assert rc == 0, out
    assert lastmod_of(repo, "glossary.html") == "2026-01-01"

    # Правим страницу, НЕ коммитим — так работает pre-commit hook.
    (repo / "docs" / "glossary.html").write_text("<html>edited</html>\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/glossary.html"], cwd=repo, check=True,
                   capture_output=True, env=_base_env())

    rc, out = run_script(repo, "--commit-date", "2026-02-02")
    assert rc == 0, out
    assert lastmod_of(repo, "glossary.html") == "2026-02-02", (
        "файл из индекса получил не дату коммита — хук воспроизведёт падение CI"
    )


def test_unstaged_page_keeps_history_date(repo):
    """Страница вне индекса берёт дату из истории, а не из --commit-date."""
    (repo / "docs" / "faq.html").write_text("<html>edited</html>\n", encoding="utf-8")
    rc, out = run_script(repo, "--commit-date", "2026-02-02")
    assert rc == 0, out
    assert lastmod_of(repo, "faq.html") == "2026-01-01", (
        "незакоммиченная и не поставленная в индекс правка попала в lastmod"
    )


def test_hook_then_commit_passes_check(repo):
    """Полный цикл: хук сгенерировал, коммит прошёл — CI-проверка зелёная.

    Именно эта связка падала на батче C: генерация до коммита и проверка
    после считали разные даты для одной и той же страницы.
    """
    rc, _ = run_script(repo)
    assert rc == 0
    commit_all(repo, "initial sitemap", "2026-01-01T00:00:00")

    (repo / "docs" / "glossary.html").write_text("<html>edited</html>\n", encoding="utf-8")
    (repo / "docs" / "calculator.html").write_text("<html>edited</html>\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/glossary.html", "docs/calculator.html"],
                   cwd=repo, check=True, capture_output=True, env=_base_env())

    # Хук передаёт `date +%Y-%m-%d` — ту же дату, что получит коммит.
    # Тест фиксирует обе, иначе рассинхрон был бы искусственным.
    rc, out = run_script(repo, "--commit-date", "2026-03-03")
    assert rc == 0, out
    git(repo, "add", "docs/sitemap.xml")
    git(repo, "commit", "-q", "-m", "page edits", date="2026-03-03")

    rc, out = run_script(repo, "--check")
    assert rc == 0, f"CI-проверка упала бы после коммита хуком:\n{out}"


# --------------------------------------------------------------------------
# Баг 2: самоссылка главной страницы.
# --------------------------------------------------------------------------


def test_homepage_lastmod_is_not_self_referential(repo):
    """Коммит, меняющий только sitemap.xml, не должен ломать --check."""
    rc, out = run_script(repo)
    assert rc == 0, out
    commit_all(repo, "initial sitemap", "2026-01-01T00:00:00")

    before = lastmod_of(repo, "")

    # Правка САМОЙ главной, чтобы её дата сдвинулась.
    (repo / "docs" / "index.html").write_text("<html>v2</html>\n", encoding="utf-8")
    commit_all(repo, "index edit", "2026-04-04")

    # Генерируем ПОСЛЕ коммита — ровно так поступает CI на чистом checkout.
    rc, out = run_script(repo)
    assert rc == 0, out
    assert lastmod_of(repo, "") == "2026-04-04"
    assert lastmod_of(repo, "") != before

    # Теперь коммит, меняющий ТОЛЬКО sitemap.xml, датой в будущем.
    commit_all(repo, "sitemap only", "2026-05-05")

    rc, out = run_script(repo, "--check")
    assert rc == 0, (
        "коммит, затронувший только sitemap.xml, делает sitemap устаревшим — "
        "lastmod главной берётся по docs/, а это «любой файл», включая сам "
        f"sitemap.xml:\n{out}"
    )


def test_homepage_tracks_index_html_not_directory(repo):
    """Правка страницы, КРОМЕ главной, не двигает lastmod главной."""
    rc, _ = run_script(repo)
    assert rc == 0
    commit_all(repo, "initial sitemap", "2026-01-01T00:00:00")

    (repo / "docs" / "faq.html").write_text("<html>v2</html>\n", encoding="utf-8")
    rc, out = run_script(repo)
    assert rc == 0, out

    assert lastmod_of(repo, "") == "2026-01-01", (
        "lastmod главной среагировал на правку faq.html — путь строится "
        "по каталогу docs/, а не по файлу index.html"
    )


# --------------------------------------------------------------------------
# Защитные проверки CLI.
# --------------------------------------------------------------------------


def test_check_and_commit_date_are_mutually_exclusive(repo):
    rc, out = run_script(repo, "--check", "--commit-date", "2026-02-02")
    assert rc != 0
    assert "детерминирован" in out or "нет смысла" in out


def test_bad_commit_date_rejected(repo):
    rc, out = run_script(repo, "--commit-date", "вчера")
    assert rc != 0
    assert "не дата" in out


def test_generation_is_idempotent(repo):
    rc, first = run_script(repo)
    assert rc == 0
    rc, second = run_script(repo)
    assert rc == 0
    assert first.split("sha256 ")[-1] == second.split("sha256 ")[-1]


def test_every_entry_points_at_a_real_file(repo):
    """source из collect() обязан быть файлом на диске.

    Пустой source (главная) раньше превращался в pathspec «docs/».
    """
    for _loc, source, _freq, _prio in bs.collect():
        if source:
            assert (bs.DOCS / source).is_file(), f"нет файла: {source}"


def test_real_docs_sitemap_is_current():
    """Живой docs/sitemap.xml совпадает с генератором — то же, что ждёт CI."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_sitemap.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stdout
