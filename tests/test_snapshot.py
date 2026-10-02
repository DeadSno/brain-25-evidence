"""Слепок docs/data.json — защита от незаметной мутации данных.

QA_AUDIT P1 (саморемонт). Раньше тест в двух случаях завершался `return` без
`assert`: при UPDATE_SNAPSHOT=1 и при отсутствии файла слепка. Оба случая давали
ЗЕЛЁНЫЙ прогон, то есть «проверка» ничего не проверяла — достаточно было один раз
поставить переменную окружения, и дрейф данных становился невидимым.

Теперь:
  UPDATE_SNAPSHOT=1 → перезапись слепка и SKIP с явным текстом (подсвечено, не спрятано)
  слепка нет        → FAIL с инструкцией (это ошибка репозитория, а не «первый прогон»)
  слепок есть       → сравнение и assert
"""
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
SNAP = ROOT / "tests" / "snapshot_data.json"


def test_snapshot_unchanged():
    assert DATA.exists(), f"нет файла данных: {DATA}"
    cur = json.loads(DATA.read_text(encoding="utf-8"))

    if os.environ.get("UPDATE_SNAPSHOT") == "1":
        SNAP.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
        # Не return: зелёный результат здесь означал бы «проверка пройдена»,
        # хотя проверка не выполнялась. SKIP виден в отчёте и в CI.
        pytest.skip(
            "snapshot перезаписан по UPDATE_SNAPSHOT=1 — проверка НЕ выполнялась. "
            "Просмотрите diff и закоммитируйте новый слепок."
        )

    assert SNAP.exists(), (
        f"Слепок отсутствует: {SNAP}. Это не «первый прогон», а потерянный файл в репозитории. "
        "Восстановить его: git checkout -- tests/snapshot_data.json, "
        "либо пересоздать осознанно: UPDATE_SNAPSHOT=1 python -m pytest tests/test_snapshot.py"
    )

    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    assert cur == snap, (
        "data.json изменился относительно слепка! "
        "Если это осознанно: UPDATE_SNAPSHOT=1 python -m pytest tests/test_snapshot.py -q"
    )
