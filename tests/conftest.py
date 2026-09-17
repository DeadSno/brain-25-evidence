"""Общие фикстуры для тестов brain-25-evidence."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def data_json_path(project_root: Path) -> Path:
    return project_root / "docs" / "data.json"
