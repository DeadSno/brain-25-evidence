"""e2e PART B (PWA): manifest+SW+офлайн-фолбэк data.json.

Изолированный прогон PWA-части (не зависит от e2e_smoke и чужих веток).
Сервер — python http.server на порту 8124 (docs/).
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PORT = 8124
BASE = f"http://localhost:{PORT}"


def main() -> None:
    n_all = len(json.loads((DOCS / "data.json").read_text(encoding="utf-8")))
    print(f"[part-b] http.server port={PORT}, карточек в data.json={n_all}", flush=True)

    srv = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "-d", str(DOCS)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # readiness check
    for _ in range(20):
        try:
            urlopen(f"{BASE}/index.html", timeout=2)
            break
        except URLError:
            time.sleep(0.3)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            print("[part-b] 1/4 загрузка index.html (online, первичная)", flush=True)
            pg.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=8000)
            pg.wait_for_function("window.chart != null", timeout=8000)

            # B4: manifest + theme-color в head
            mlink = pg.locator("link[rel='manifest']").get_attribute("href")
            assert mlink and mlink.endswith("manifest.webmanifest"), f"нет link manifest: {mlink!r}"
            mcolor = pg.locator('meta[name="theme-color"]').get_attribute("content")
            assert mcolor == "#1c1c1e", f"theme-color: {mcolor!r}"
            print(f"[part-b]     manifest={mlink!r}  theme-color={mcolor!r}", flush=True)

            # B5: SW зарегистрирован — ждём claim() на первой странице (до 10s),
            # затем делаем контролируемый reload ?ts= (данные пойдут через SW → кэш v27-data)
            print("[part-b] 2/4 ждём SW-контроллер (~10с), затем контролируемый reload", flush=True)
            pg.wait_for_function(
                "() => navigator.serviceWorker && navigator.serviceWorker.controller !== null",
                timeout=10000,
            )
            ctrl = pg.evaluate("navigator.serviceWorker.controller !== null")
            assert ctrl, "SW не управляет страницей"
            scope = pg.evaluate(
                "navigator.serviceWorker.controller?.scope ?? navigator.serviceWorker.controller?.scope"
            )
            print(f"[part-b]     controller ok, scope={scope!r}", flush=True)
            ts = int(time.time())
            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            assert pg.evaluate(
                "navigator.serviceWorker.controller !== null"
            ), "контролируемый reload: controller === null — данные пойдут мимо SW"

            # провоцируем кэширование data.json network-first и ждём, пока оно уляжется в кэш
            pg.wait_for_function(
                """() => caches.open('v27-data')
                       .then(c => c.keys())
                       .then(ks => ks.some(r => r.url.endsWith('/data.json')))""",
                timeout=8000,
            )
            assert not errors, f"ошибки консоли (online): {errors}"

            # B3: офлайн — reload в том же контексте (SW per-origin)
            print("[part-b] 3/4 офлайн: context.set_offline(True), reload, фолбэк data.json", flush=True)
            assert pg.locator("script[src='pwa.js']").count() == 1, "pwa.js не подключён"
            pg.context.set_offline(True)
            try:
                pg.reload(wait_until="domcontentloaded")
                time.sleep(0.5)
                badge = pg.locator("#pwaOfflineBadge")
                badge.wait_for(state="attached", timeout=8000)
                assert badge.count() == 1, "нет бейджа «офлайн-режим»"
                badge_txt = badge.inner_text()
                assert "Офлайн-режим" in badge_txt, f"текст бейджа: {badge_txt!r}"
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=8000)
                n_off = pg.locator(".card[data-id]").count()
                assert n_off == n_all, f"офлайн карточек {n_off}, ожидалось {n_all}"
                ttl = pg.evaluate("document.title")
                ctrl_off = pg.evaluate("navigator.serviceWorker.controller !== null")
                print(f"[part-b]     badge={badge_txt!r}  cards={n_off}  sw_controller={ctrl_off}  title={ttl!r}",
                      flush=True)
            finally:
                pg.context.set_offline(False)
                pg.wait_for_timeout(1500)
                ts += 1
                pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=10000)
                pg.wait_for_function("window.chart != null", timeout=10000)
                hidden = pg.locator("#pwaOfflineBadge").count() == 0
                print(f"[part-b]     online restore: badge_hidden={hidden}", flush=True)
                assert hidden, "бейдж не скрылся после online"

            # map.html: pwa.js подключён
            print("[part-b] 4/4 map.html: pwa.js подключён", flush=True)
            pg.goto(f"{BASE}/map.html", wait_until="domcontentloaded")
            pg.wait_for_selector("#chain", state="attached", timeout=5000)
            assert pg.locator("script[src='pwa.js']").count() == 1, "map.html без pwa.js"
            print("[part-b]     map.html pwa.js OK", flush=True)

            b.close()
    finally:
        srv.terminate()
    print("[part-b] e2e PART B (pwa): OK")


if __name__ == "__main__":
    main()