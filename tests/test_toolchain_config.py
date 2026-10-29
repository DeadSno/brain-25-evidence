"""Конфигурация инструмента агента (opencode.json) должна быть разбираема.

Зачем этот тест
---------------
ROADMAP #101: «watchdog не проверяет MCP/Serena». Замер показал, что
формулировка неточна: `serena` и `uvx` в `.github/workflows/watchdog.yml`
действительно не встречаются, но и проверять там нечего — блока `mcp`
в `opencode.json` репозитория нет вообще (файл содержит только
`$schema` и `lsp`), конфигурация MCP живёт в пользовательском
каталоге, которого CI не видит.

Поэтому предмет проверки заменён на тот, который существует и который
действительно ломает работу тихо: **сам файл конфигурации**.

Что ломается незаметно
----------------------
`opencode.json` читается не при старте агента, а лениво, и ошибка в нём
не даёт ни одного сообщения — сессия просто продолжает работать без
языкового сервера, без плагинов, без MCP. Всё выглядит живо. Единственная
точка, где файл читается целиком и падает при ошибке, — это CI, и до
этого теста её не существовало: watchdog гонял только `test_schema.py`
и `test_site_data.py`, то есть данные сайта, но не инструментарий.

Тест написан так, чтобы покрыть и `mcp`: с v5.6.5 блок объявлен в
репозитории в формате OpenCode V2 (`mcp.servers.<name>`), и
`test_mcp_block_is_absent_or_wellformed` фиксирует это явно, а не
молча пропускает. Поддерживаются оба формата — V1 (`mcp.<name>`) и
V2 (`mcp.servers.<name>`); разбор — в `_server_configs`.

Про PATH
--------
Разрешение команд в PATH проверяется только когда окружение позволяет.
В CI тулчейн не ставится, и требование `pyright-langserver` в PATH там
не выполнимо — тест в этом случае скипает с объяснением, а не падает.
Локально у владельца оба сервера в PATH (проверено 2026-10-07), поэтому
проверка работает по-настоящему.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "opencode.json"

#: Ключи верхнего уровня, без которых конфиг не имеет смысла.
#: v5.6.4: `provider` убран из перечня. Он был обязательным только потому,
#: что в `provider` жил единственный провайдер — openrouter, отключённый
#: в v5.6.1 (`opencode auth logout openrouter`, переменная окружения
#: удалена). Ссылка на несуществующую переменную окружения — это ровно тот
#: мёртвый декларативный блок, за который этот же тест ругает `mode`
#: в скиллах. Провайдера в конфиге больше нет, и требовать его нельзя:
#: иначе гейт требовал бы вернуть то, что удалено намеренно.
REQUIRED_KEYS = {"$schema", "lsp"}

#: Блоки, чьи команды должны разрешаться. `mcp` был добавлен заранее —
#: на случай, если владелец перенесёт декларацию MCP в репозиторий; в
#: v5.6.5 это произошло (`mcp.servers.mcp-mermaid`), и проверка
#: заработала без правок этого списка.
COMMAND_BLOCKS = ("lsp", "mcp")

IN_CI = os.environ.get("CI", "").lower() in {"1", "true", "yes"}


def _config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _server_configs(block_data: dict):
    """Yield (name, cfg) pairs from a command block.

    Supports both V1 format (block.<name> -> cfg) and V2 format
    (block.servers.<name> -> cfg), the latter being the OpenCode V2
    `mcp.servers` schema.
    """
    servers = block_data.get("servers")
    if isinstance(servers, dict):
        yield from servers.items()
    else:
        yield from block_data.items()


def test_config_is_valid_json():
    """Плохой JSON здесь означает молчаливо отключённый тулчейн."""
    assert CONFIG.exists(), (
        f"{CONFIG.name} не найден. Без него агент стартует без "
        f"языковых серверов, и никто об этом не узнаёт."
    )
    data = _config()
    assert isinstance(data, dict), "конфиг должен быть объектом JSON"


def test_required_top_level_keys_present():
    data = _config()
    missing = sorted(REQUIRED_KEYS - set(data))
    assert not missing, (
        f"В {CONFIG.name} нет ключей: {', '.join(missing)}. "
        f"Каждый из них влияет на работу, и его отсутствие не даёт "
        f"никакой диагностики."
    )


def test_declared_commands_are_wellformed():
    """Каждая команда — непустой массив строк.

    Пустой список или строка вместо массива означают, что сервер
    объявлен, но не запускается.
    """
    data = _config()
    for block in COMMAND_BLOCKS:
        entries = data.get(block)
        if entries is None:
            continue
        assert isinstance(entries, dict), f"{block} должен быть объектом"
        for name, cfg in _server_configs(entries):
            assert isinstance(cfg, dict), f"{block}.{name} должен быть объектом"
            cmd = cfg.get("command")
            assert isinstance(cmd, list) and cmd, (
                f"{block}.{name}.command должен быть непустым массивом, "
                f"получено {cmd!r}"
            )
            assert all(isinstance(part, str) and part for part in cmd), (
                f"{block}.{name}.command содержит пустую часть: {cmd!r}"
            )


def test_secrets_use_env_indirection():
    """Ключи и токены — только через {env:...}, литералов быть не должно."""
    data = _config()
    offenders: list[str] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() in {"apikey", "api_key", "token", "secret", "password"}:
                    if isinstance(v, str) and not v.startswith("{env:"):
                        offenders.append(f"{path}.{k}")
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(data, CONFIG.name)
    assert not offenders, (
        f"Секрет записан литералом вместо ссылки на переменную: "
        f"{', '.join(offenders)}. Используй {{env:ИМЯ}}."
    )


def test_declared_commands_resolve_in_path():
    """Команды из конфига должны запускаться.

    Пропускается в CI: туда тулчейн не ставится, и требование
    `pyright-langserver` в PATH невыполнимо по построению.
    """
    data = _config()
    declared = [
        cfg["command"][0]
        for block in COMMAND_BLOCKS
        if isinstance(data.get(block), dict)
        for name, cfg in _server_configs(data[block])
        if isinstance(cfg, dict) and cfg.get("command")
    ]
    assert declared, (
        "В конфиге не объявлено ни одной команды - проверять нечего. "
        "Это само по себе признак, что конфиг потерян."
    )
    missing = sorted({cmd for cmd in declared if not shutil.which(cmd)})
    if missing:
        if IN_CI:
            import pytest
            pytest.skip(
                f"CI не ставит тулчейн, команды {', '.join(missing)} "
                f"в PATH не ожидаются. Проверка полноценно работает "
                f"локально."
            )
        assert not missing, (
            f"Команда из конфига не найдена в PATH: {', '.join(missing)}. "
            f"Сервер объявлен, но не запустится - и сессия продолжит "
            f"работу без него молча."
        )


def test_mcp_block_is_absent_or_wellformed():
        """Фиксирует текущее состояние по MCP.

        Блок `mcp` объявлен в v5.6.5 (V2-формат `mcp.servers`), но тест
        по-прежнему не требует его наличия: это решение владельца. Он
        лишь не пропускает тему молча — если блок есть, к нему
        применяются все проверки выше.
        """
        data = _config()
        assert "mcp" not in data or isinstance(data["mcp"], dict), (
            "Блок mcp должен быть объектом, если он объявлен."
        )