"""Манифест PWA: обязательные поля есть, объявленные ссылки существуют.

Зачем поле `id` (TR-P1-02)
-------------------------
Спецификация Web App Manifest требует `id` явно. Без него браузер
выводит идентификатор из `start_url` — и делает это не всегда так,
как ожидает разработчик: смена `start_url` молча меняет `id`, то
есть браузер считает приложение ДРУГИМ и не обновляет уже
установленное (новое окно поверх старого, старая иконка в меню).

Проверка не в том, что `id` есть, — в том, что он стабилен к
`start_url` и к `scope`: их смена обязана быть осознанным решением.

Зачем проверять, что файлы из манифеста существуют
--------------------------------------------------
`icons[].src` и `shortcuts[].url` — это обещание, которое браузер
проверит только в момент установки. Отсутствующий файл даёт
молчаливый отказ: иконка не рисуется, ярлык открывает 404. В
репозитории это выглядит безобидно, пока не проверить.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MANIFEST = DOCS / "manifest.webmanifest"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_is_valid_json(manifest):
    assert manifest, "манифест пуст"


def test_manifest_has_explicit_id(manifest):
    """TR-P1-02: `id` обязан быть объявлен явно."""
    assert "id" in manifest, (
        "В манифесте нет поля id. По спецификации оно выводится из "
        "start_url, и при смене start_url идентификатор меняется молча "
        "- браузер считает приложение новым."
    )
    assert isinstance(manifest["id"], str) and manifest["id"].strip()


def test_manifest_id_is_not_derived_from_start_url(manifest):
    """Смысл проверки: id не должен повторять start_url."""
    assert manifest.get("id") != manifest.get("start_url"), (
        "id совпадает со start_url - это ровно тот случай, от которого "
        "поле id и защищает: смена start_url уведёт за собой id."
    )


def test_manifest_required_members_present(manifest):
    required = ("name", "short_name", "start_url", "scope", "display", "icons")
    missing = [k for k in required if k not in manifest]
    assert not missing, f"в манифесте нет обязательных полей: {missing}"


def test_manifest_declared_files_exist(manifest):
    """Каждая объявленная ссылка обязана существовать на диске.

    Иначе иконка не рисуется, а ярлык открывает 404 - но только в
    момент установки, то есть у пользователя, не у нас в CI.
    """
    missing: list[str] = []
    for icon in manifest.get("icons", []):
        src = icon.get("src")
        if src and not (DOCS / src.lstrip("./")).is_file():
            missing.append(f"icons: {src}")
    for sc in manifest.get("shortcuts", []):
        url = sc.get("url")
        if url and not (DOCS / url.lstrip("./")).is_file():
            missing.append(f"shortcuts[{sc.get('short_name')}]: {url}")
        for icon in sc.get("icons", []):
            src = icon.get("src")
            if src and not (DOCS / src.lstrip("./")).is_file():
                missing.append(f"shortcuts[{sc.get('short_name')}]: {src}")
    assert not missing, "объявлено, но не существует:\n" + "\n".join(missing)


def test_shortcuts_are_wellformed(manifest):
    """У каждого ярлыка есть имя и url; имена не повторяются."""
    shortcuts = manifest.get("shortcuts")
    if not shortcuts:
        pytest.skip("shortcuts не объявлены")
    seen: set[str] = set()
    for sc in shortcuts:
        for key in ("name", "short_name", "url"):
            assert sc.get(key), f"в ярлыке нет поля {key}: {sc}"
        assert sc["short_name"] not in seen, (
            f"дубль short_name у ярлыков: {sc['short_name']} - в меню "
            f"установленных приложений они станут неразличимыми"
        )
        seen.add(sc["short_name"])


def test_screenshots_were_deliberately_omitted(manifest):
    """Явный контракт: поля `screenshots` нет, и это зафиксировано.

    По спецификации `screenshots` необязателен, но он единственный
    член манифеста, который требует БИНАРНЫХ ассетов (снимков
    экрана). Их в репозитории нет, и генерировать их молча нельзя:
    это решение владельца (что показывать в диалоге установки), а не
    технический долг.

    Проверка падает, если поле появится из ниоткуда - тогда решение
    принято, и этот тест надо переписать под проверку самих снимков
    (файл существует, размеры из sizes реальны).
    """
    assert "screenshots" not in manifest, (
        "В манифесте появилось поле screenshots, которого решали не "
        "быть. Значит решение принято - перепишите этот тест так, "
        "чтобы он проверял снимки: файл существует, а размеры из "
        "sizes совпадают с реальными размерами картинки."
    )