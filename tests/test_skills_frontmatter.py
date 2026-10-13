"""Frontmatter скиллов должен соответствовать конвенции проекта.

Зачем этот тест
---------------
SK-P2-01 требовал поле `compatibility` у 18 скиллов. Замер показал, что
требование перенесено из чужой схемы: `compatibility` есть ровно у
одного скилла — вендорного `cyberaudit` (ArisRoman, v3.1.5), и в
репозитории на него не ссылается вообще ни одна строка кода,
конфиг или скрипт.

Конвенция самого проекта — другая, и её соблюдают все 19 своих
скиллов: `name`, `description`, `license`, `version`, `updated`,
`project`. Дописывать поле `compatibility` в 19 файлов значило бы
добавить мёртвый метаданный: ровно то, за что SK-P2-02 ругает
декоративный `mode`. Закрытие долга — не добавить поле, а зафиксировать
настоящую конвенцию гейтом, чтобы следующий аудит не поднял тот же
ложный флаг, а новое поле не появилось снова незамеченным.

Что проверяется
---------------
1. У каждого скилла есть `SKILL.md` с frontmatter, ограниченным
   `---` с обеих сторон.
2. `name` совпадает с именем каталога: иначе скилл грузится под одним
   именем, а вызывается под другим, и ошибка проявляется как
   «скилл не найден».
3. `description` непустой — именно по нему агент решает, грузить ли
   тело скилла в контекст.
4. Свои скиллы имеют `version`, `updated`, `project`; `project`
   совпадает с именем репозитория; `updated` — дата не из будущего.
5. Ключ вне разрешённого набора запрещён. Сверх обязательного
   разрешены только поля вендорного cyberaudit, и у каждого
   записано, почему. `mode` больше не разрешён (F-38): поле было
   в ALLOWED_EXTRA с обоснованием «рантайм его читает» — замер
   схемы показал, что скиллы разбирают только name, description,
   slash, а `mode` из SKILL.md молча отбрасывается.
6. Вендорные скиллы перечислены с причиной и обязаны сохранять
   собственную схему, а не молча переходить на проектную.
7. Страховка от схлопывания: скиллов должно быть не меньше 20
   (замер 2026-10-12: ровно 20).
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".opencode" / "skills"
PROJECT = "brain-25-evidence"

#: Минимальный набор для скилла проекта.
REQUIRED = ("name", "description", "license", "version", "updated", "project")

#: Ключи сверх REQUIRED, каждый с причиной.
#: Ключи сверх REQUIRED, каждый с причиной. Ключ сюда попадает либо
#: потому что его читает рантайм, либо потому что он принадлежит
#: вендорному скиллу и сносится при повторном вендоринге.
#:
#: Про `mode` (F-38, SK-P2-02): поле было в ALLOWED_EXTRA с
#: обоснованием «рантайм читает его, это не декорация». Обоснование
#: было неверным, и нашлось это замером схемы рантайма в бинарнике
#: opencode.exe, а не чтением документации.
#:
#: Схема скиллов (SkillV2.load) разбирает ровно три поля:
#:     Struct({ name, description, slash })
#: и кладёт в реестр только {name, description, slash, location,
#: content}. `mode` в эту структуру не входит и молча отбрасывается.
#: Поле `mode` существует в другой схеме — frontmatter АГЕНТОВ
#: (.opencode/agent/*.md): там mode ∈ primary | subagent | all.
#: То есть в SKILL.md оно выглядело как работающая настройка, а
#: работало как ничего. Ровно тот декоративный метаданный, который
#: аудит и ругал; гейт это закреплял вместо того, чтобы чинить.
#: Поле удалено из SKILL.md и из ALLOWED_EXTRA — вернуться не сможет.
#:
#: Для полноты: `slash` рантайм действительно читает, но в проекте
#: не используется. Если понадобится — вносить сюда с причиной.
ALLOWED_EXTRA = {
    "compatibility": "схема вендорного cyberaudit, в проекте не читается "
                     "нигде; оставлено как есть, чтобы вендор не расходился "
                     "с оригиналом",
    "metadata": "вложенный блок вендорного cyberaudit (author, version, "
                "allowed-tools)",
}

#: Скиллы, принесённые извне. Для них конвенция проекта не применяется.
VENDORED = {
    "cyberaudit": "сторонний навык (ArisRoman, v3.1.5, 130+ файлов). "
                  "Правка frontmatter разойдётся при повторном "
                  "вендоринге, поэтому фиксируем его схему как есть.",
}

TOP_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):")


def _frontmatter(path: Path) -> dict[str, str]:
    """Разбирает верхний уровень frontmatter.

    Полный YAML здесь не нужен и был бы хуже: во вложенных блоках
    (`metadata:`) отступ есть, поэтому такие строки под верхний уровень
    не попадают.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{path.name}: frontmatter не открыт строкой ---")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(f"{path.name}: frontmatter не закрыт строкой ---")
    out: dict[str, str] = {}
    for line in lines[1:end]:
        m = TOP_KEY.match(line)
        if m:
            out.setdefault(m.group(1), line[m.end():].strip())
    return out


def _skills() -> list[Path]:
    return sorted(p.parent for p in SKILLS.glob("*/SKILL.md"))


def test_every_skill_has_parsable_frontmatter():
    assert SKILLS.is_dir(), f"каталог скиллов не найден: {SKILLS}"
    dirs = sorted(d.name for d in SKILLS.iterdir() if d.is_dir())
    broken = []
    for name in dirs:
        md = SKILLS / name / "SKILL.md"
        if not md.exists():
            broken.append(f"{name}: нет SKILL.md")
            continue
        try:
            _frontmatter(md)
        except AssertionError as e:
            broken.append(f"{name}: {e}")
    assert not broken, "скилл с нечитаемым frontmatter:\n" + "\n".join(broken)


def test_name_matches_directory():
    """Имя скилла обязано совпадать с именем каталога."""
    wrong = []
    for d in _skills():
        fm = _frontmatter(d / "SKILL.md")
        if fm.get("name") != d.name:
            wrong.append(f"{d.name}: name={fm.get('name')!r}")
    assert not wrong, (
        "name не совпадает с именем каталога:\n" + "\n".join(wrong)
        + "\nСкилл грузится под именем из name, а каталог называется иначе — "
          "это расхождение проявляется как «скилл не найден»."
    )


def test_description_is_present():
    """По description агент решает, грузить ли тело скилла в контекст."""
    empty = [
        d.name for d in _skills()
        if not _frontmatter(d / "SKILL.md").get("description")
    ]
    assert not empty, (
        f"Пустой description у: {', '.join(empty)}. Без него скилл не "
        f"будет выбран — тело не грузится, и выглядит это как «скилл "
        f"молчит»."
    )


def test_project_skills_follow_convention():
    missing = []
    wrong_project = []
    future = []
    today = date.today()
    for d in _skills():
        if d.name in VENDORED:
            continue
        fm = _frontmatter(d / "SKILL.md")
        absent = [k for k in REQUIRED if k not in fm]
        if absent:
            missing.append(f"{d.name}: нет {', '.join(absent)}")
        if fm.get("project") != PROJECT:
            wrong_project.append(f"{d.name}: project={fm.get('project')!r}")
        raw = fm.get("updated", "")
        try:
            when = date.fromisoformat(raw)
        except ValueError:
            future.append(f"{d.name}: updated={raw!r} не дата ISO")
            continue
        if when > today:
            future.append(f"{d.name}: updated={raw} в будущем")
    assert not missing, (
        "Скилл не соблюдает конвенцию проекта:\n" + "\n".join(missing)
        + f"\nОбязательные поля: {', '.join(REQUIRED)}."
    )
    assert not wrong_project, (
        "Неверный project:\n" + "\n".join(wrong_project)
        + f"\nОжидается {PROJECT!r}."
    )
    assert not future, "Некорректный updated:\n" + "\n".join(future)


def test_no_unexpected_frontmatter_keys():
    """Новое поле не должно появляться незамеченным.

    Декоративный метаданный — это ровно то, что сейчас ругает аудит
    в SK-P2-02. Ключ, которого нет в ALLOWED_EXTRA, не читается ничем:
    он молча ничего не делает, пока кто-то не решит, что делает.
    """
    allowed = set(REQUIRED) | set(ALLOWED_EXTRA)
    unknown: list[str] = []
    for d in _skills():
        for key in _frontmatter(d / "SKILL.md"):
            if key not in allowed:
                unknown.append(f"{d.name}.{key}")
    assert not unknown, (
        f"Поля frontmatter вне конвенции: {', '.join(unknown)}.\n"
        f"Разрешено: {', '.join(sorted(allowed))}.\n"
        f"Если поле нужно — добавь его в REQUIRED или ALLOWED_EXTRA "
        f"с причиной, иначе это мёртвый метаданный."
    )


def test_vendored_skills_keep_their_own_schema():
    """Вендорный скилл не должен молча перейти на проектную схему."""
    for name, reason in VENDORED.items():
        d = SKILLS / name
        assert d.is_dir(), f"{name} помечен вендорным, но каталога нет"
        fm = _frontmatter(d / "SKILL.md")
        assert "metadata" in fm, (
            f"{name} числится вендорным и должен сохранять свой блок "
            f"metadata. Если он переписан под проектную схему — убери "
            f"его из VENDORED и объясни почему. Причина вендоринга: "
            f"{reason}"
        )


def test_skill_inventory_does_not_shrink():
    """Страховка от молчаливого уменьшения числа скиллов."""
    n = len(_skills())
    assert n >= 20, (
        f"Найдено {n} скиллов, ожидалось не меньше 20 "
        f"(замер 2026-10-12: 20). Похоже, разбор SKILLS.glob сломан."
    )
