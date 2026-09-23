"""A3.2.3-фаза-2: Playwright headful для PDF, где curl_cffi упал.

headless=True блокируется Akamai у MDPI/OUP/T&F. Используем headful.
Требуется открытый рабочий стол. Гонять порциями днём.

Использование:
    python scripts\\fetch_fulltexts_playwright.py --limit 10
    python scripts\\fetch_fulltexts_playwright.py --workers 2
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from playwright_stealth import Stealth

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

PAPERS = ROOT / "data" / "papers" / "papers.json"
UNPAYWALL = ROOT / "data" / "papers" / "unpaywall.json"
OUT_DIR = ROOT / "data" / "pmc"
TEXT_DIR = OUT_DIR / "text"
TMP_DIR = OUT_DIR / "tmp"
INDEX = OUT_DIR / "index.json"

MIN_TEXT_CHARS = 500
MAX_SIZE = 30 * 1024 * 1024


def extract_pdf_text(pdf_path: Path) -> tuple[str | None, int]:
    try:
        doc = pymupdf.open(pdf_path)
        pages = doc.page_count
        text = "\n".join(p.get_text("text") for p in doc).strip()
        doc.close()
        return text, pages
    except Exception:
        return None, 0


def fetch_via_browser(page, url: str, dest: Path) -> tuple[bool, str]:
    """Открывает PDF-URL через download handler."""
    try:
        with page.expect_download(timeout=60000) as dl_info:
            page.goto(url, timeout=30000, wait_until="commit")
        download = dl_info.value
        download.save_as(dest)

        # Проверка размера
        if dest.stat().st_size > MAX_SIZE:
            return False, "too_big"
        with open(dest, "rb") as f:
            head = f.read(4)
        if head != b"%PDF":
            return False, "not_pdf"
        return True, ""
    except PWTimeout:
        return False, "pw_timeout"
    except Exception as e:
        return False, f"pw_err_{type(e).__name__}"


def process_one(pmid: str, pdf_url: str, workers: int) -> dict:
    """Каждый вызов — свой браузер (для параллелизма)."""
    pdf_path = TMP_DIR / f"{pmid}.pdf"
    txt_path = TEXT_DIR / f"{pmid}.txt"

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Europe/Moscow",
            accept_downloads=True,
        )
        page = ctx.new_page()

        ok, err = fetch_via_browser(page, pdf_url, pdf_path)
        browser.close()

    if not ok:
        return {"status": "failed", "pdf_error": err, "source": pdf_url}

    text, pages = extract_pdf_text(pdf_path)
    try:
        pdf_path.unlink()
    except Exception:
        pass

    if not text or len(text) < MIN_TEXT_CHARS:
        return {"status": "failed", "pdf_error": "extract_failed",
                "pages": pages, "source": pdf_url}

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(text, encoding="utf-8")
    return {"status": "ok", "type": "pdf_playwright",
            "pages": pages, "chars": len(text), "source": pdf_url}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2,
                    help="Параллельных браузеров (2-3, не больше)")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    unpaywall = json.loads(UNPAYWALL.read_text(encoding="utf-8"))
    index: dict = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}

    # Расширенный фильтр: включаем все ошибки, кроме пропускаемых
    SKIP_ERRORS = ("404", "http_401", "http_418", "too_big", "DNSError")
    tasks: list[tuple[str, str]] = []
    for pmid, rec in index.items():
        if rec.get("status") == "ok":
            continue
        err = rec.get("pdf_error") or rec.get("error") or ""
        # Пропускаем если хоть одна из SKIP_ERRORS встречается
        if any(s in err for s in SKIP_ERRORS):
            continue
        # Пропускаем уже неуспешные через Playwright (не зацикливаемся)
        if rec.get("type") == "pdf_playwright":
            continue
        doi = (papers.get(pmid) or {}).get("doi")
        if not doi:
            continue
        u = unpaywall.get(doi) or {}
        pdf_url = u.get("pdf")
        if pdf_url:
            tasks.append((pmid, pdf_url))

    if args.limit:
        tasks = tasks[: args.limit]

    print(f"К обработке (headful): {len(tasks)}")
    print(f"Потоков:               {args.workers}")
    print(f"ВНИМАНИЕ: откроются окна Chromium — не закрывайте их.")
    print()

    if not tasks:
        print("[OK] Нет задач")
        return 0

    t0 = time.time()
    done = ok = err = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_one, pmid, url, args.workers): pmid
                   for pmid, url in tasks}
        for fut in as_completed(futures):
            pmid = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": "failed", "error": str(e)}
            index[pmid] = result
            done += 1
            if result.get("status") == "ok":
                ok += 1
            else:
                err += 1

            if done % 10 == 0:
                INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(tasks) - done) / rate if rate else 0
                print(f"[{done}/{len(tasks)}] ok={ok} err={err} · "
                      f"{rate:.2f} files/s · ETA {eta/60:.1f} мин")

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] ok={ok}, err={err}, время {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())