"""Тесты scripts/build_feed.py — ловят баг, из-за которого CI падал 2026-10-09.

До v5.6.4 фида в pre-commit хуке не было вовсе: хук пересобирал только
sitemap.xml, а дата записи каталога sup/index.html бралась из `git log`.
Поэтому ЛЮБОЙ коммит, затронувший docs/sup/index.html, делал
закоммиченный docs/feed.xml устаревшим на один день — генератор начинал
считать каталог изменённым с даты этого коммита, а файл в репозитории
отставал на один. CI падал на шаге «Feed check».

Замерено 2026-10-09: расходились ровно две строки — <lastBuildDate> и
<pubDate> каталога (08 → 09 Oct 2026); остальные 130 записей совпали
до байта, то есть дело было ровно в датах, а не в содержимом.

Лечится `--commit-date` — тем же приёмом, что и в build_sitemap.py, и по
той же причине: `git log` не видит незакоммиченные правки, поэтому файл
из индекса получил бы дату своего ПРЕДЫДУЩЕГО коммита.

Сеть не используется. git вызывается по-настоящему, но только на временном
клоне из tmp_path: живой репозиторий тесты не трогают.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_feed as bf  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="нужен git")


# --------------------------------------------------------------------------
# Фикстура: минимальный клон с data.json, docs/sup/ и генератором.
# --------------------------------------------------------------------------


#: Переменные git, которые НЕЛЬЗЯ наследовать от окружения теста.
#:
#: Замерено 2026-10-09: pre-commit хук запускается git'ом, и git передаёт
#: хуку `GIT_DIR` (и заодно GIT_INDEX_FILE). Фикстура копировала os.environ
#: в дочерний git, поэтому `git init` в tmp_path НЕ создавал репозиторий
#: вообще — он переинициализировал ЖИВОЙ репозиторий проекта. Дальше
#: `git add -A` и `git commit` писали в его индекс и историю: HEAD уехал
#: на фикстурный коммит «initial», а docs/*.html и docs/data.json в
#: рабочем дереве оказались содержимым фикстуры.
#:
#: Вне хука то же самое выглядит зелёным — переменных в окружении нет,
#: клон создаётся, тесты проходят. Именно поэтому баг дожил до v5.6.4:
#: он воспроизводится только внутри `git commit`.
GIT_ENV_TO_DROP = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_QUARANTINE_PATH",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_CONFIG",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
    "GIT_PREFIX",
)


def _base_env():
    import os

    env = dict(os.environ)
    for key in GIT_ENV_TO_DROP:
        env.pop(key, None)
    # Детерминированные даты: тест не должен зависеть от «сегодня».
    env.pop("GIT_AUTHOR_DATE", None)
    env.pop("GIT_COMMITTER_DATE", None)
    env["TZ"] = "UTC"
    # Кодировка вывода генератора задаётся явно — иначе дочерний Python на
    # Windows возьмёт кодировку консоли (cp1251/cp866) и русские сообщения
    # об ошибках превратятся в «кракозябры». Тот же приём и с PYTHONIOENCODING,
    # что в tests/test_build_sitemap.py:97.
    env["PYTHONIOENCODING"] = "utf-8"
    return env


@pytest.fixture()
def repo(tmp_path):
    """Репозиторий с data.json, двумя карточками и генератором из этого дерева."""
    import json

    root = tmp_path / "repo"
    (root / "docs" / "sup").mkdir(parents=True)
    (root / "docs" / "sup" / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (root / "docs" / "sup" / "aaa.html").write_text("<html></html>\n", encoding="utf-8")
    (root / "docs" / "sup" / "bbb.html").write_text("<html></html>\n", encoding="utf-8")

    records = [
        {"name": "ААА", "code": 1, "about": "первая", "category": "x", "updated": "2026-01-01"},
        {"name": "БББ", "code": 2, "about": "вторая", "category": "y", "updated": "2026-01-02"},
    ]
    (root / "docs" / "data.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    scripts = root / "scripts"
    scripts.mkdir()
    shutil.copy(ROOT / "scripts" / "build_feed.py", scripts / "build_feed.py")
    # build_feed импортирует slugify и text из build_sup — без него
    # генератор не запустится вовсе.
    shutil.copy(ROOT / "scripts" / "build_sup.py", scripts / "build_sup.py")

    git(root, "init", "-q")
    # Падение здесь означало бы утечку GIT_* из окружения (см. GIT_ENV_TO_DROP):
    # `git init` не создал бы клон, а переинициализировал живой репозиторий.
    # Проверяем ДО первого git add, чтобы ущерб ограничивался этой строкой.
    assert (root / ".git").is_dir(), (
        "git init не создал репозиторий в tmp_path — GIT_DIR унаследован "
        "из окружения, клон пишет в живой репозиторий проекта"
    )
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    commit_all(root, "initial", "2026-01-01")
    return root


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


def run_script(repo, *args):
    """Запустить генератор в клоне, вернуть (returncode, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "build_feed.py"), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_base_env(),
    )
    return proc.returncode, proc.stdout + proc.stderr


def catalog_pubdate(repo):
    """<pubDate> записи каталога — единственной, чья дата берётся из git."""
    text = (repo / "docs" / "feed.xml").read_text(encoding="utf-8")
    blocks = text.split("<item>")
    for block in blocks:
        if f"{bf.BASE}sup/index.html</link>" in block:
            return block.split("<pubDate>")[1].split("</pubDate>")[0]
    raise AssertionError("нет записи каталога в feed.xml")


def card_pubdate(repo, slug):
    """<pubDate> карточки."""
    text = (repo / "docs" / "feed.xml").read_text(encoding="utf-8")
    for block in text.split("<item>"):
        if f"{bf.BASE}sup/{slug}.html</link>" in block:
            return block.split("<pubDate>")[1].split("</pubDate>")[0]
    raise AssertionError(f"нет {slug} в feed.xml")


# --------------------------------------------------------------------------
# Главный сценарий: файл из индекса получает дату коммита, а не прошлую.
# --------------------------------------------------------------------------


def test_staged_catalog_gets_commit_date_not_previous(repo):
    """Сценарий хука: sup/index.html в индексе + --commit-date."""
    rc, out = run_script(repo)
    assert rc == 0, out
    assert catalog_pubdate(repo).startswith("Thu, 01 Jan 2026")

    # Правим каталог, НЕ коммитим — так работает pre-commit hook.
    (repo / "docs" / "sup" / "index.html").write_text("<html>edited</html>\n", encoding="utf-8")
    git(repo, "add", "docs/sup/index.html")

    rc, out = run_script(repo, "--commit-date", "2026-02-02")
    assert rc == 0, out
    assert catalog_pubdate(repo).startswith("Mon, 02 Feb 2026"), (
        "каталог из индекса получил не дату коммита — хук воспроизведёт "
        "падение CI, ровно как это случилось с sitemap"
    )


def test_unstaged_catalog_keeps_history_date(repo):
    """Каталог вне индекса берёт дату из истории, а не из --commit-date."""
    (repo / "docs" / "sup" / "index.html").write_text("<html>edited</html>\n", encoding="utf-8")

    rc, out = run_script(repo, "--commit-date", "2026-02-02")
    assert rc == 0, out
    assert catalog_pubdate(repo).startswith("Thu, 01 Jan 2026"), (
        "незакоммиченная и не поставленная в индекс правка попала в pubDate — "
        "--commit-date начнёт затирать дату истории у файлов, которых в "
        "коммите не будет"
    )


def test_commit_date_does_not_touch_cards(repo):
    """--commit-date не влияет на карточки: их pubDate из data.json.

    Проверка на то, что флаг не разошёлся шире нужного: если бы он
    подставлялся всем записям, дата карточек зависела бы от того, в какой
    день сделан коммит, — то есть фид менялся бы сам собой при каждом
    коммите, даже когда данные не трогали.
    """
    before = card_pubdate(repo, "aaa") if (repo / "docs" / "feed.xml").is_file() else None
    if before is None:
        rc, out = run_script(repo)
        assert rc == 0, out
        before = card_pubdate(repo, "aaa")

    rc, out = run_script(repo, "--commit-date", "2026-02-02")
    assert rc == 0, out
    assert card_pubdate(repo, "aaa") == before, (
        "дата карточки поехала за --commit-date — источник у неё data.json"
    )


def test_hook_then_commit_passes_check(repo):
    """Полный цикл: хук сгенерировал, коммит прошёл — CI-проверка зелёная.

    Именно эта связка падала 2026-10-09: генерация до коммита и проверка
    после считали разные даты для одной и той же записи каталога.
    """
    rc, out = run_script(repo)
    assert rc == 0, out
    commit_all(repo, "initial feed", "2026-01-01")

    (repo / "docs" / "sup" / "index.html").write_text("<html>edited</html>\n", encoding="utf-8")
    git(repo, "add", "docs/sup/index.html")

    # Хук передаёт `date +%Y-%m-%d` — ту же дату, что получит коммит.
    # Тест фиксирует обе, иначе рассинхрон был бы искусственным.
    rc, out = run_script(repo, "--commit-date", "2026-03-03")
    assert rc == 0, out
    git(repo, "add", "docs/feed.xml")
    git(repo, "commit", "-q", "-m", "catalog edit", date="2026-03-03")

    rc, out = run_script(repo, "--check")
    assert rc == 0, f"CI-проверка упала бы после коммита хуком:\n{out}"


def test_hook_without_commit_date_is_detected(repo):
    """Проверка ловит именно тот дефект, который закрывает --commit-date.

    Тест на сам генератор, а не на хук: он коммитит каталог и держит в
    файле дату, посчитанную ДО коммита — то есть ровно то состояние, в
    котором оказывался репозиторий без feed в хуке. `--check` обязан
    сказать «расшёлся».
    """
    rc, out = run_script(repo)
    assert rc == 0, out
    commit_all(repo, "initial feed", "2026-01-01")

    (repo / "docs" / "sup" / "index.html").write_text("<html>edited</html>\n", encoding="utf-8")
    git(repo, "add", "docs/sup/index.html")
    # Генерируем БЕЗ --commit-date — так работал бы наивный хук.
    rc, out = run_script(repo)
    assert rc == 0, out
    git(repo, "add", "docs/feed.xml")
    git(repo, "commit", "-q", "-m", "catalog edit", date="2026-03-03")

    rc, out = run_script(repo, "--check")
    assert rc != 0, (
        "--check не заметил устаревшего фида — гейт на расхождение выключен"
    )
    assert "разошёлся" in out


# --------------------------------------------------------------------------
# Защитные проверки CLI — те же, что у build_sitemap.py.
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


def test_live_docs_feed_is_current():
    """Живой docs/feed.xml совпадает с генератором — то же, что ждёт CI."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_feed.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stdout