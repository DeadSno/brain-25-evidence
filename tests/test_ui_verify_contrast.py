"""Математика пробы контраста из scripts/ui_verify.py (A11Y-P2-04).

Находка A11Y-P2-04: `_effective_bg` поднимался вверх по DOM, глядя только на
`backgroundColor`, поэтому любой градиентный слой терялся. Для элементов с
прозрачным фоном проба возвращала `--bg` и проверяла контраст на цвете,
которого под текстом нет: `body::before` (z-index: -2) кладёт поверх фона
страницы mesh из трёх radial-gradient.

Проба теперь считает худший из достижимых фонов, и вся арифметика вынесена на
уровень модуля — её можно проверить без браузера и без живого сервера.
Именно это и делает тест ниже: иначе единственной проверкой был
бы сам `scripts/ui_verify.py`, а он ещё и красный с 2026-10-01 (ждёт бейдж
`.noPrice`, удалённый коммитом a1f1653) — то есть новая логика контраста
не проверялась бы ничем.

Запуск:    pytest -q tests/test_ui_verify_contrast.py
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

pytest.importorskip("playwright.sync_api", reason="playwright не установлен")

from ui_verify import (  # noqa: E402 — sys.path настраивается выше
    _collect_bg_stack,
    _contrast,
    _gradient_stops,
    _parse_css_color,
    _paint_order,
    _worst_case_bg,
)

STYLE_CSS = ROOT / "docs" / "style.css"

#: Реальные значения из docs/style.css — не выдуманные, иначе тест проверял бы
#: не тот код, который работает на сайте.
MESH = (
    "radial-gradient(600px 400px at 15% 10%, rgba(52,152,219,.16), transparent 60%), "
    "radial-gradient(700px 500px at 85% 20%, rgba(155,89,182,.14), transparent 60%), "
    "radial-gradient(800px 600px at 50% 95%, rgba(46,204,113,.10), transparent 60%)"
)
SKELETON = "linear-gradient(100deg, rgba(128,128,128,.12) 40%, rgba(128,128,128,.28) 50%, rgba(128,128,128,.12) 60%)"


# ───────────────────────────── разбор цвета ─────────────────────────────

@pytest.mark.parametrize("css,expected", [
    ("#fff", (255, 255, 255, 1.0)),
    ("#ffffff", (255, 255, 255, 1.0)),
    ("#000000ff", (0, 0, 0, 1.0)),
    ("#f582be", (245, 130, 190, 1.0)),
    ("rgb(31, 111, 165)", (31, 111, 165, 1.0)),
    ("rgba(127, 127, 127, .14)", (127, 127, 127, 0.14)),
    ("rgba(0, 0, 0, 0)", (0, 0, 0, 0.0)),
    ("rgb(127 127 127 / 14%)", (127, 127, 127, 0.14)),
    ("transparent", (0, 0, 0, 0.0)),
    ("white", (255, 255, 255, 1.0)),
])
def test_parse_css_color_understands_common_forms(css, expected):
    parsed = _parse_css_color(css)
    assert parsed is not None, css
    assert parsed == pytest.approx(expected)


@pytest.mark.parametrize("css", [
    None, "", "   ", "currentColor", "var(--bg)", "hsl(210 50% 40%)",
    "#ff", "#fffff", "не цвет", "rgba(",
])
def test_parse_css_color_refuses_to_guess(css):
    """Лучше «не знаю», чем выдуманный цвет: выдумка молча проходит assert."""
    assert _parse_css_color(css) is None


# ───────────────────────────── градиенты ─────────────────────────────

def test_gradient_stops_of_nothing_is_empty():
    assert _gradient_stops("none") == []
    assert _gradient_stops("") == []
    assert _gradient_stops(None) == []


def test_gradient_stops_two_color_linear():
    stops = _gradient_stops("linear-gradient(135deg, #f1c40f, #f39c12)")
    assert stops == [(241, 196, 15, 1.0), (243, 156, 18, 1.0)]


def test_gradient_stops_project_mesh_has_all_layers():
    """body::before — три слоя, и каждый даёт два стопа (цвет + transparent)."""
    stops = _gradient_stops(MESH)
    assert stops is not None
    assert len(stops) == 6
    assert stops[0][3] == pytest.approx(0.16)
    assert stops[1][3] == 0.0  # transparent 60% — вклад ноль, но он учтён
    assert [round(s[3], 2) for s in stops] == [0.16, 0.0, 0.14, 0.0, 0.10, 0.0]


def test_gradient_stops_project_skeleton_animated():
    stops = _gradient_stops(SKELETON)
    assert stops is not None
    assert [round(s[3], 2) for s in stops] == [0.12, 0.28, 0.12]


@pytest.mark.parametrize("image", [
    "url('noise.svg')",
    "linear-gradient(to right, url('a.png'), #fff)",
    "color-mix(in srgb, #3498db 14%, transparent)",
    "conic-gradient(from 0deg, oklch(70% .1 200), #fff)",
])
def test_gradient_stops_reports_unparsable_instead_of_pretending(image):
    """Фон-картинка или color-mix() — это None, а не «пусто»: проба обязана
    сказать вслух, что не разобрала слой, иначе она вернёт выдуманный фон."""
    assert _gradient_stops(image) is None


def test_every_gradient_in_style_css_is_parsed():
    """Гейт на сам проект: если в docs/style.css появится фон, который проба
    не понимает, она начнёт считать контраст по выдуманной подложке — и
    находка A11Y-P2-04 вернётся в новом виде."""
    css = STYLE_CSS.read_text(encoding="utf-8")
    # Значения живут в именованных токенах (`--grad-*` в `:root`), а правила
    # ссылаются на них через `background: var(--grad-x)`. Проба контраста
    # работает на computed styles браузера, где var() уже развёрнут; здесь его
    # надо развернуть руками, иначе гейт увидит «фон без градиента».
    tokens = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;{}]+)", css))

    def _resolve(value: str) -> str:
        return re.sub(
            r"var\((--[\w-]+)\)",
            lambda m: tokens.get(m.group(1), m.group(0)),
            value,
        )

    gradients = [
        _resolve(m.group(1).strip())
        for m in re.finditer(r"background(?:-image)?\s*:\s*([^;{}]+)", css)
        if "gradient(" in _resolve(m.group(1))
    ]
    # 4 объявления, 13 слоёв: .btn.calc (2 стопа), .skeleton (3),
    # body::before (3 radial — 6 стопов), .bestBadge (2).
    # Нижняя граница нужна, чтобы гейт не прошёл «успехом» на пустом совпадении —
    # ровно та ловушка, из-за которой «74 skipped выглядит как успех».
    layers = sum(len(_gradient_stops(g) or []) for g in gradients)
    assert len(gradients) >= 4 and layers >= 6, (
        f"градиентов в docs/style.css: объявлений {len(gradients)}, слоёв {layers}; "
        "ожидалось не меньше 4 и 6. Либо стиль переехал, либо regex перестал видеть "
        "background — проверь, прежде чем править число"
    )
    unparsed = [g for g in gradients if _gradient_stops(g) is None]
    assert not unparsed, (
        "проба контраста не разбирает эти фоны из docs/style.css — "
        "дополни _gradient_stops или убери фон:\n" + "\n".join(unparsed)
    )


# ───────────────────────────── разбор стека фонов ─────────────────────────────
#
# Ниже — реальный стек, снятый с живой страницы (docs/index.html, тёмная
# тема, ссылка в футере). Именно на нём воспроизводилась находка: старая
# проба дошла до `body` и вернула rgb(28, 28, 30), потеряв и mesh из
# body::before, и «непонятный» url-шум из body::after.


def _layer(tag, bg="rgba(0, 0, 0, 0)", image="none", opacity=1.0, pseudos=None):
    return {"tag": tag, "bg": bg, "image": image, "opacity": opacity,
            "pseudos": pseudos or []}


REAL_STACK = [
    _layer("a"),
    _layer("p", opacity=0.85),
    _layer("footer", opacity=0.85),
    _layer("body", "rgb(28, 28, 30)", pseudos=[
        _layer("body::before", image=MESH),
        _layer("body::after", image='url("data:image/svg+xml,<svg/>")', opacity=0.04),
    ]),
    _layer("html"),
]


def test_paint_order_puts_pseudo_above_its_own_background():
    order = [l["tag"] for l in _paint_order(REAL_STACK)]
    assert order == [
        "html", "body", "body::before", "body::after", "footer", "p", "a",
    ]


def test_stack_base_is_body_and_mesh_becomes_overlay():
    base, overlays, unparsed = _collect_bg_stack(REAL_STACK)
    assert base == (28, 28, 30)
    # 4 стопа с ненулевой альфой из mesh: .16, .14, .10 и… три transparent
    # дают 0 и в overlays не попадают
    assert overlays == [(52, 152, 219, 0.16), (155, 89, 182, 0.14), (46, 204, 113, 0.10)]
    assert unparsed == ["body::after"]


def test_gradient_below_opaque_layer_is_hidden():
    """Непрозрачный предок скрывает всё, что под ним, включая градиент."""
    stack = [
        _layer("a"),
        _layer("div", "rgb(255, 255, 255)"),
        _layer("body", "rgb(28, 28, 30)", pseudos=[_layer("body::before", image=MESH)]),
        _layer("html"),
    ]
    base, overlays, unparsed = _collect_bg_stack(stack)
    assert base == (255, 255, 255)
    assert overlays == [], "градиент под непрозрачной подложкой не виден"
    assert unparsed == []


def test_gradient_on_the_base_itself_is_counted():
    """`background: linear-gradient(...)` рисуется поверх своего же
    background-color — иначе .btn.calc и .bestBadge проверялись бы вхолостую."""
    stack = [
        _layer("a"),
        _layer("span", "rgb(255, 255, 255)",
               image="linear-gradient(135deg, #f1c40f, #f39c12)"),
        _layer("html"),
    ]
    base, overlays, _ = _collect_bg_stack(stack)
    assert base == (255, 255, 255)
    assert overlays == [(241, 196, 15, 1.0), (243, 156, 18, 1.0)]


def test_layer_opacity_scales_overlay_alpha():
    stack = [
        _layer("a"),
        _layer("body", "rgb(255, 255, 255)", pseudos=[
            _layer("body::before", "rgba(0, 0, 0, .5)", opacity=0.5),
        ]),
        _layer("html"),
    ]
    _base, overlays, _ = _collect_bg_stack(stack)
    assert overlays == [(0, 0, 0, 0.25)]


def test_stack_without_any_opaque_layer():
    base, overlays, unparsed = _collect_bg_stack([_layer("a"), _layer("html")])
    assert base is None
    assert overlays == []
    assert unparsed == []


# ───────────────────────────── худший фон ─────────────────────────────

def test_contrast_known_values():
    assert _contrast("#000", "#fff") == pytest.approx(21.0, abs=0.01)
    assert _contrast("#fff", "#fff") == pytest.approx(1.0, abs=0.01)


def test_worst_case_never_gentler_than_base():
    """Отбор худшего не может сделать контраст ЛУЧШЕ, чем было без градиента."""
    fg = "rgb(245, 245, 247)"
    base = (28, 28, 30)
    overlays = [(52, 152, 219, 0.16), (155, 89, 182, 0.14), (46, 204, 113, 0.10)]
    rgb, _why = _worst_case_bg(fg, base, overlays)
    assert _contrast(fg, "rgb(%d, %d, %d)" % tuple(rgb)) <= _contrast(fg, "rgb(%d, %d, %d)" % base)


def test_regression_light_gradient_was_invisible_before():
    """Собственно находка A11Y-P2-04: mesh на тёмной теме осветляет подложку,
    и светлый текст на ней хуже, чем на голом --bg. Старая проба возвращала
    ровно --bg и этого не видела."""
    fg = "rgb(245, 245, 247)"       # --text в тёмной теме
    base = (28, 28, 30)              # --bg в тёмной теме
    mesh = [(52, 152, 219, 0.16), (155, 89, 182, 0.14), (46, 204, 113, 0.10)]

    rgb, why = _worst_case_bg(fg, base, mesh)
    worst = "rgb(%d, %d, %d)" % tuple(rgb)

    assert sum(rgb) > sum(base), "осветляющие слои должны осветлять подложку"
    assert "осветляющ" in why, why
    assert _contrast(fg, worst) < _contrast(fg, "rgb(28, 28, 30)")


def test_darkening_overlay_picked_for_dark_text():
    fg = "rgb(28, 28, 30)"
    base = (245, 245, 247)
    rgb, why = _worst_case_bg(fg, base, [(0, 0, 0, 0.30)])
    assert sum(rgb) < sum(base)
    assert "затемняющ" in why, why


def test_no_overlays_returns_base_itself():
    rgb, why = _worst_case_bg("rgb(0,0,0)", (10, 20, 30), [])
    assert rgb == (10, 20, 30)
    assert why == "подложка"