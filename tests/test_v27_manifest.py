"""v2.7 PWA: manifest.webmanifest — валидный JSON с обязательными полями + иконки."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "manifest.webmanifest"
ICONS_DIR = ROOT / "docs" / "icons"


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_valid_json():
    m = _load()
    assert isinstance(m, dict) and m


def test_manifest_required_fields_non_empty():
    m = _load()
    for field in ("name", "short_name", "start_url", "display"):
        assert m.get(field), f"поле {field} пустое или отсутствует"
        assert str(m[field]).strip(), f"поле {field} пустое"


def test_manifest_display_standalone():
    assert _load()["display"] == "standalone"


def test_manifest_icons_two_with_sizes():
    m = _load()
    icons = m.get("icons")
    assert isinstance(icons, list) and len(icons) >= 2, "нужно минимум 2 иконки"
    sizes = []
    for icon in icons:
        assert icon.get("type") == "image/png", "иконка не PNG"
        assert icon.get("src"), "у иконки нет src"
        assert icon.get("sizes"), "у иконки нет sizes"
        assert icon["sizes"] in ("192x192", "512x512")
        sizes.append(icon["sizes"])
    assert "192x192" in sizes and "512x512" in sizes


def test_manifest_icon_files_exist():
    m = _load()
    for icon in m["icons"]:
        rel = icon["src"].lstrip("./")
        png = ROOT / "docs" / rel
        assert png.exists(), f"иконка {png} не существует"
        assert png.stat().st_size > 0, f"иконка {png} пустая (0 байт)"


def test_manifest_colors():
    m = _load()
    assert m.get("background_color"), "нет background_color"
    assert m.get("theme_color"), "нет theme_color"
    for c in (m["background_color"], m["theme_color"]):
        assert c.startswith("#") and len(c) == 7, f"цвет {c!r} не в формате #RRGGBB"