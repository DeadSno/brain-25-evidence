"""Гард: все JS в docs/ должны парситься (node --check)."""
import shutil
import subprocess
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
NODE = shutil.which("node")
JS_FILES = sorted(p.name for p in DOCS.glob("*.js"))


@pytest.mark.skipif(NODE is None, reason="node не установлен")
@pytest.mark.parametrize("js", JS_FILES)
def test_js_syntax(js):
    r = subprocess.run([NODE, "--check", str(DOCS / js)],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"{js}: SyntaxError:\n{r.stderr}"
