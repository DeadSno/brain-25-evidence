"""UI-verify (ранбук шаг 5): noPrice/empty/toTop в живой вёрстке + скриншоты 1280/375."""
import re, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
SHOTS = Path(__file__).resolve().parents[1] / "reports" / "ui"
BASE = "http://localhost:8123"


# ============ контраст: разбор цвета и композитинг фонов (A11Y-P2-04) ============
#
# До v5.6.5 проба `_effective_bg` смотрела ТОЛЬКО на `backgroundColor` и
# поднималась вверх по DOM до непрозрачного слоя. Градиенты при этом
# терялись, хотя в проекте они есть всегда: `body::before` (z-index: -2) —
# mesh из трёх radial-gradient, плюс `.btn.calc` (linear-gradient),
# `.bestBadge` (linear-gradient), `.skeleton` (анимированный linear-gradient).
#
# Что это значило на деле: для любого элемента с прозрачным фоном проба
# возвращала `--bg` и считала, что под текстом лежит ровно он. На деле под
# текстом — `--bg` с подмешанным градиентом, т.е. другая яркость и другой
# контраст. Проверка «контраст ≥ 4.5» на прозрачных элементах проходила
# на выдуманном фоне.
#
# Теперь проба собирает весь стек фонов (элемент → предки → их ::before и
# ::after) и возвращает ХУДШИЙ из возможных результатов: без наложений, все
# затемняющие слои, все осветляющие, все вместе. Худший — значит
# гарантированно не заниженный контраст: проба может ошибиться в сторону
# «нашла проблему там, где её нет», но не в сторону «не заметила».
#
# Чего проба НЕ умеет и говорит об этом вслух: фон-картинка (`url(...)`),
# `color-mix()` и любой незнакомый цвет. Для таких слоёв она возвращает их
# в `unparsed`, и подпись попадает в текст assert'а — раньше такие фоны
# просто не учитывались.

_COLOR_RE = re.compile(
    r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b"
    r"|rgba?\([^()]*\)"
    r"|hsla?\([^()]*\)"
    r"|\btransparent\b"
    r"|\b(?:white|black|silver|gray|grey|red|green|blue|yellow|orange|purple)\b",
    re.IGNORECASE,
)

_NAMED_COLORS = {
    "white": (255, 255, 255), "black": (0, 0, 0), "silver": (192, 192, 192),
    "gray": (128, 128, 128), "grey": (128, 128, 128), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0),
    "orange": (255, 165, 0), "purple": (128, 0, 128),
}

#: Что проба принципиально не разбирает. Наличие такого слоя — не ошибка,
#: но он обязан попасть в `unparsed`, чтобы подпись об этом видна.
_OPAQUE_BG_FUNCTIONS = (
    "url(", "color-mix(", "image-set(", "-webkit-image-set(",
    "oklch(", "oklab(", "lab(", "lch(", "hwb(", "color(",
)


def _parse_css_color(color):
    """CSS-цвет -> (r, g, b, a) или None, если формат не понимаем.

    Понимает `#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, `rgb()`, `rgba()`,
    `rgb(r g b / a)`, `transparent` и одиннадцать именованных. Всё
    остальное (hsl, oklch, var, currentColor) -> None: выдумывать цвет
    опаснее, чем сказать «не знаю».
    """
    if not color:
        return None
    color = color.strip()
    low = color.lower()
    if low == "transparent":
        return (0, 0, 0, 0.0)
    if low in _NAMED_COLORS:
        r, g, b = _NAMED_COLORS[low]
        return (r, g, b, 1.0)
    if color.startswith("#"):
        h = color[1:]
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        if len(h) not in (6, 8):
            return None
        try:
            parts = [int(h[i:i + 2], 16) for i in range(0, len(h), 2)]
        except ValueError:
            return None
        alpha = parts[3] / 255.0 if len(parts) == 4 else 1.0
        return (parts[0], parts[1], parts[2], alpha)
    if low.startswith(("rgb(", "rgba(")):
        try:
            inner = low[low.index("(") + 1:low.rindex(")")]
        except ValueError:
            return None
        parts = [p for p in re.split(r"[,/\s]+", inner) if p]
        percent = len(parts) > 3 and parts[3].endswith("%")
        if percent:
            parts[3] = parts[3][:-1]
        try:
            nums = [float(p) for p in parts[:4]]
        except ValueError:
            return None
        while len(nums) < 3:
            nums.append(255.0)
        alpha = (nums[3] / 100.0 if percent else nums[3]) if len(nums) > 3 else 1.0
        return (nums[0], nums[1], nums[2], min(1.0, max(0.0, alpha)))
    return None


def _srgb_lin(x):
    x /= 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    """Относительная яркость по WCAG."""
    return 0.2126 * _srgb_lin(rgb[0]) + 0.7152 * _srgb_lin(rgb[1]) + 0.0722 * _srgb_lin(rgb[2])


def _contrast(fg, bg):
    """Контраст двух цветов: CSS-строками или кортежами (r, g, b).

    Непонимаемый цвет -> 128,128,128, как и раньше: значение заведомо
    среднее, чтобы assert не прошёл/упал по воле случая.
    """
    def _as_rgb(c):
        if isinstance(c, (tuple, list)):
            return tuple(c[:3])
        parsed = _parse_css_color(c)
        return parsed[:3] if parsed else (128, 128, 128)

    L1, L2 = _lum(_as_rgb(fg)), _lum(_as_rgb(bg))
    if L1 < L2:
        L1, L2 = L2, L1
    return (L1 + 0.05) / (L2 + 0.05)


def _gradient_stops(background_image):
    """Цветовые стопы всех слоёв `background-image`.

    `[]`   — фона нет (`none`) или градиент без стопов (не бывает).
    `None` — фон есть, но разобрать его нельзя: `url(...)` (картинка),
            `color-mix(...)`, незнакомый цвет. Вызывающий обязан сказать
            об этом вслух, а не считать подложку сплошной.
    """
    if not background_image or background_image == "none":
        return []
    low = background_image.lower()
    if any(fn in low for fn in _OPAQUE_BG_FUNCTIONS):
        return None
    if "gradient(" not in low:
        return None
    stops = []
    for match in _COLOR_RE.finditer(background_image):
        parsed = _parse_css_color(match.group(0))
        if parsed is None:
            return None
        stops.append(parsed)
    return stops or None


def _blend(base, overlay):
    """Полупрозрачный слой поверх подложки (alpha-blending, без гаммы)."""
    r, g, b, a = overlay
    return (base[0] * (1 - a) + r * a,
            base[1] * (1 - a) + g * a,
            base[2] * (1 - a) + b * a)


def _worst_case_bg(fg, base, overlays):
    """Худший для контраста фон из возможных -> (rgb, подпись).

    Градиент не имеет одного цвета: у него есть диапазон. Поэтому вместо
    одного «примерного» цвета считаем четыре достижимых состояния и берём
    то, где контраст минимален:
      * подложка сама по себе (градиента нет);
      * подложка + все затемняющие слои;
      * подложка + все осветляющие слои;
      * подложка + все слои вместе.
    """
    base_lum = _lum(base)
    dark, light = [], []
    for overlay in overlays:
        (dark if _lum(overlay[:3]) < base_lum else light).append(overlay)

    def _chain(layers):
        out = base
        for layer in layers:
            out = _blend(out, layer)
        return out

    cases = [("подложка", base)]
    if dark:
        cases.append(("+ затемняющие слои", _chain(dark)))
    if light:
        cases.append(("+ осветляющие слои", _chain(light)))
    if overlays:
        cases.append(("+ все слои", _chain(overlays)))
    why, rgb = min(cases, key=lambda kv: _contrast(fg, kv[1]))
    return rgb, why


#: Собирает стек фонов вокруг элемента: сам элемент и все предки, у каждого —
#: собственный фон и фоны его ::before/::after. Порядок — сверху вниз
#: (элемент первым); порядок отрисовки восстанавливает `_paint_order`.
_EFFECTIVE_BG_JS = r"""
(sel) => {
  const transparent = (c) => c === 'rgba(0, 0, 0, 0)' || c === 'transparent';
  const read = (tag, st) => ({
    tag: tag,
    bg: st.backgroundColor,
    image: st.backgroundImage,
    opacity: parseFloat(st.opacity) || 1,
    pseudos: []
  });
  const el = document.querySelector(sel);
  if (!el) return null;
  const stack = [];
  let node = el;
  while (node) {
    const base_tag = node.nodeName.toLowerCase() + (node.id ? '#' + node.id : '');
    const layer = read(base_tag, getComputedStyle(node));
    for (const pe of ['::before', '::after']) {
      const p = getComputedStyle(node, pe);
      if (p.content !== 'none' && p.content !== 'normal'
          && (p.backgroundImage !== 'none' || !transparent(p.backgroundColor))) {
        layer.pseudos.push(read(base_tag + pe, p));
      }
    }
    stack.push(layer);
    node = node.parentElement;
  }
  return { fg: getComputedStyle(el).color, stack: stack };
}
"""


def _paint_order(stack):
    """Стек «сверху вниз» -> порядок отрисовки «снизу вверх».

    Псевдоэлемент рисуется ПОВЕРХ собственного фона своего узла, поэтому в
    развёрнутом стеке `body::before` должен идти сразу за `body`, а не перед
    ним. Порядок важен: непрозрачный слой скрывает всё, что ниже него, и
    ошибиться здесь — значит приписать элементу чужой фон.
    """
    order = []
    for layer in reversed(stack):
        order.append(layer)
        order.extend(layer.get("pseudos") or [])
    return order


def _collect_bg_stack(stack):
    """Порядок отрисовки -> (подложка, наложения, неразобранные слои).

    Подложка — первый непрозрачный `background-color` снизу вверх; всё, что
    ниже него, скрыто и в расчёт не идёт. Наложения — полупрозрачные цвета и
    цветовые стопы градиентов выше подложки (включая градиент самой подложки:
    `background: linear-gradient(...)` рисуется поверх `background-color`).
    """
    base, overlays, unparsed = None, [], []
    for layer in _paint_order(stack):
        color = _parse_css_color(layer["bg"])
        if color and color[3] >= 0.999:
            # Непрозрачный слой скрывает всё, что ниже него, — включая
            # градиент предка. Он же становится новой подложкой.
            base, overlays, unparsed = color[:3], [], []
        elif base is None:
            continue  # ниже непрозрачной подложки ничего не видно
        opacity = layer.get("opacity") or 1.0
        image = layer.get("image") or "none"
        if image != "none":
            stops = _gradient_stops(image)
            if stops is None:
                unparsed.append(layer["tag"])
            else:
                for r, g, b, a in stops:
                    if a * opacity > 0:
                        overlays.append((r, g, b, a * opacity))
        if color and 0 < color[3] < 1:
            overlays.append((color[0], color[1], color[2], color[3] * opacity))
    return base, overlays, unparsed


def _effective_bg(pg_js, sel):
    """Худший реальный фон под элементом с учётом градиентов.

    Возвращает `{"fg", "bg", "note", "unparsed"}` либо None, если элемента
    нет. `bg` — строка `rgb(r, g, b)`, годная для `_contrast`, и всегда
    та, при которой контраст минимален. `note` объясняет, откуда она
    взялась, — она попадает в текст assert'а, чтобы «проба не заметила»
    больше нельзя было спутать с «проба проверила».
    """
    data = pg_js.evaluate(_EFFECTIVE_BG_JS, sel)
    if not data:
        return None
    fg = data["fg"]
    base, overlays, unparsed = _collect_bg_stack(data["stack"])

    if base is None:
        # Край страницы: непрозрачной подложки нет вовсе. Раньше здесь
        # возвращался последний (прозрачный) цвет, который _contrast читал
        # как 128,128,128 — тоже выдумка, просто другая.
        rgb, why = min(
            (("белая", (255, 255, 255)), ("чёрная", (0, 0, 0))),
            key=lambda kv: _contrast(fg, kv[1]),
        )
        return {"fg": fg, "bg": "rgb(%d, %d, %d)" % tuple(rgb),
                "note": f"непрозрачной подложки нет, взят худший из {why}",
                "unparsed": [l["tag"] for l in _paint_order(data["stack"])]}

    rgb, why = _worst_case_bg(fg, base, overlays)
    note = f"{why} из {len(overlays)} полупрозрачных слоёв"
    if unparsed:
        note += f"; НЕ разобрано: {', '.join(unparsed)}"
    return {"fg": fg, "bg": "rgb(%d, %d, %d)" % tuple(round(v) for v in rgb),
            "note": note, "unparsed": unparsed}


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8123", "-d", str(DOCS)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
            pg.wait_for_selector(".card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)

            # бейдж noPrice в вёрстке (26 товаров без цены)
            np_count = pg.locator(".noPrice").count()
            assert np_count >= 1, "бейдж noPrice не отрендерен"

            # пустое состояние: поиск мусором → .empty + #resetAll
            pg.locator("#search").fill("zzzqqqнесуществующийxyz")
            assert pg.locator(".empty").count() == 1, "empty state не показан"
            assert pg.locator("#resetAll").is_visible(), "кнопка resetAll не видна"

            # сброс возвращает карточки с бейджем
            pg.locator("#resetAll").click()
            assert pg.locator(".noPrice").count() == np_count, "сброс не вернул бейджи"

            # #toTop появляется при скролле
            assert pg.locator("#toTop").count() == 1, "#toTop отсутствует в DOM"
            pg.evaluate("window.scrollTo(0, 1200)")
            pg.wait_for_timeout(300)
            assert "show" in (pg.locator("#toTop").get_attribute("class") or ""), \
                "#toTop не получил .show после скролла"

            pg.screenshot(path=str(SHOTS / "ui_1280.png"), full_page=True)

            # 375px (закрывает пункт C «не верифицировано»)
            pg.set_viewport_size({"width": 375, "height": 667})
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.screenshot(path=str(SHOTS / "ui_375.png"), full_page=True)
            overflow = pg.evaluate("document.documentElement.scrollWidth")
            if overflow > 380:
                print(f"WARN: горизонтальный оверфлоу на 375px: {overflow}px")

            # v2.3: баннер medium на кальций+железо
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_timeout(500)
            if pg.locator(".banner.medium").count():
                pg.screenshot(path=str(SHOTS / "banner_medium.png"))

            # v2.3: зелёная подсказка в модалке Магния
            pg.evaluate("localStorage.removeItem('favs')")
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.screenshot(path=str(SHOTS / "modal_synergy.png"))

            # v2.5: новые страницы прозрачности рендерятся и скриншотятся
            for sub in ["faq", "glossary", "changelog_public"]:
                pg.goto(f"{BASE}/{sub}.html?ts={int(time.time())}", wait_until="domcontentloaded")
                pg.wait_for_selector("h1", state="attached", timeout=5000)
                pg.screenshot(path=str(SHOTS / f"v25_{sub}.png"))

            # v2.6: главная с 5-точечными бейджами и тумблером осей
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#cardsGrid .card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.set_viewport_size({"width": 1280, "height": 900})
            pg.screenshot(path=str(SHOTS / "v26_index.png"), full_page=True)
            # переключение на ось «Число РКИ» — график перерисовался без reload
            pg.click("#axisRCT")
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(SHOTS / "v26_axisRCT.png"))
            # модалка Кофеина: точки, бейджи, поделиться/сравнить
            pg.click("#axisMA")
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(SHOTS / "v26_modal.png"), full_page=True)
            pg.keyboard.press("Escape")
            # карта с trustbar
            pg.goto(f"{BASE}/map.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#chain", state="attached", timeout=5000)
            pg.screenshot(path=str(SHOTS / "v26_map.png"), full_page=True)

            # v2.6.1: экономика-блок + топ-3 МА в модалке Кофеина
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#cardsGrid .card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.screenshot(path=str(SHOTS / "v261_index.png"), full_page=True)
            pg.locator("#sortSelect").select_option("grade")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(SHOTS / "v261_sort_grade.png"), full_page=True)
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(SHOTS / "v261_modal_economics.png"), full_page=True)
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # ==================== v2.6.2: UI-фиксы ====================
            # F3.2: скриншоты ОБЕИХ тем + контраст ссылок ≥4.5:1.
            # Вся математика контраста и сбора фонов вынесена наверх
            # (A11Y-P2-04) — она покрыта тестами без браузера.
            for theme in ["light", "dark"]:
                pg.evaluate(f"localStorage.setItem('theme', '{theme}')")
                is_dark = theme == "dark"
                if is_dark:
                    pg.evaluate("document.body.classList.add('dark')")
                else:
                    pg.evaluate("document.body.classList.remove('dark')")
                pg.wait_for_timeout(200)
                ts2 = int(time.time())
                pg.goto(f"{BASE}/index.html?ts={ts2}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
                pg.wait_for_function("window.chart != null", timeout=5000)
                prefix = f"v262_{theme}"
                pg.screenshot(path=str(SHOTS / f"{prefix}_index.png"), full_page=True)

                # контраст ссылок: footer methodology, qaMore, trustChips chip, modal srcIcon
                selectors = [
                    f"footer a[href='methodology.html']",
                    ".qaMore",
                    ".trustChips .chip",
                ]
                for sel in selectors:
                    pair = _effective_bg(pg, sel)
                    if not pair:
                        # Раньше это просто пропускалось, и проверка контраста
                        # выглядела выполненной. `.qaMore` — мёртвый класс
                        # (KNOWN_DEAD_CSS), то есть из трёх селекторов
                        # проверялись два, а отчёт об этом не говорил.
                        print(f"WARN F3.2 [{theme}] селектор не найден, "
                              f"контраст НЕ проверен: {sel}")
                        continue
                    ratio = _contrast(pair["fg"], pair["bg"])
                    assert ratio >= 4.5, (
                        f"F3.2 [{theme}] {sel}: контраст {ratio:.1f}:1 < 4.5 "
                        f"(fg={pair['fg']}, bg={pair['bg']}; {pair['note']})"
                    )

                # модалка: opening KoFein and checking modal link contrast
                pg.click(".card[data-id='Кофеин']")
                pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
                pg.wait_for_timeout(300)
                pg.screenshot(path=str(SHOTS / f"{prefix}_modal.png"), full_page=True)
                for sel in ("#modalBody .srcIcon", "#modalBody .wbLink"):
                    pair_modal = _effective_bg(pg, sel)
                    if not pair_modal:
                        print(f"WARN F3.2 [{theme}] селектор не найден, "
                              f"контраст НЕ проверен: {sel}")
                        continue
                    ratio_m = _contrast(pair_modal["fg"], pair_modal["bg"])
                    assert ratio_m >= 4.5, (
                        f"F3.2 [{theme}] {sel}: контраст {ratio_m:.1f}:1 < 4.5 "
                        f"(fg={pair_modal['fg']}, bg={pair_modal['bg']}; {pair_modal['note']})"
                    )
                pg.keyboard.press("Escape")
                pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # F5: скриншот компактных секций доверия (3 вопроса + чипы)
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            qa_box = pg.locator("#qaSection").bounding_box()
            trust_box = pg.locator("#trustSummary").bounding_box()
            if qa_box and trust_box:
                pg.screenshot(
                    path=str(SHOTS / "v262_trust_compact.png"),
                    clip={"x": 0, "y": qa_box["y"] - 10,
                          "width": 1280,
                          "height": qa_box["height"] + trust_box["height"] + 30}
                )
            # ==================== конец v2.6.2 ====================

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("UI-verify: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())