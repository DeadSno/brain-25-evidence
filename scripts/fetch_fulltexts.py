"""A3.2.3: Скачивание PDF + HTML-fallback + извлечение текста.

Стратегия для каждой статьи:
  1. Попытка скачать PDF (cloudscraper + browser headers)
  2. Если PDF = 403/404/html_response → HTML-fallback (url из unpaywall)
  3. Извлечь текст (PyMuPDF для PDF, BeautifulSoup для HTML)
  4. Сохранить data/pmc/text/<pmid>.txt

Кэш: повторный запуск не скачивает уже обработанные.

Использование:
    python scripts\\fetch_fulltexts.py --limit 20
    python scripts\\fetch_fulltexts.py
    python scripts\\fetch_fulltexts.py --workers 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import re
from urllib.parse import urlparse
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import pymupdf  # новая API
    _extract_pdf = None
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        print("[ERROR] PyMuPDF не установлен. pip install pymupdf", file=sys.stderr)
        sys.exit(1)

PAPERS = ROOT / "data" / "papers" / "papers.json"
UNPAYWALL = ROOT / "data" / "papers" / "unpaywall.json"
OUT_DIR = ROOT / "data" / "pmc"
TEXT_DIR = OUT_DIR / "text"
TMP_DIR = OUT_DIR / "tmp"
INDEX = OUT_DIR / "index.json"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,text/html;q=0.9,application/xhtml+xml;q=0.8,*/*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

MAX_PDF_SIZE = 30 * 1024 * 1024
HTTP_TIMEOUT = 60
MIN_TEXT_CHARS = 500


def _referer_for(url: str) -> str:
    """Referer: origin + путь до родительской папки."""
    parts = url.split("/")
    if len(parts) >= 3:
        return "/".join(parts[:3]) + "/"
    return url


BM_VERIFY_RE = re.compile(r'URL=[\'"]([^\'"]+)[\'"]')


def _follow_bm_verify(original_url: str, r):
    """Если пришёл bm-verify challenge — делаем второй запрос с токеном."""
    ct = r.headers.get("Content-Type", "")
    if not ct.startswith("text/html"):
        return r

    m = BM_VERIFY_RE.search(r.text[:2000])
    if not m or "bm-verify" not in m.group(1):
        return r

    next_url = m.group(1)
    if next_url.startswith("/"):
        parsed = urlparse(original_url)
        next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"

    time.sleep(5)  # meta refresh говорит 5 секунд
    return curl_requests.get(
        next_url, impersonate="chrome", timeout=HTTP_TIMEOUT,
        allow_redirects=True,
        headers={**BROWSER_HEADERS, "Referer": original_url},
    )


def download_pdf(url: str, dest: Path, scraper=None) -> tuple[bool, str]:
    """Скачивает PDF (с обработкой bm-verify)."""
    try:
        r = curl_requests.get(
            url, impersonate="chrome", timeout=HTTP_TIMEOUT,
            allow_redirects=True,
            headers={**BROWSER_HEADERS, "Referer": _referer_for(url)},
        )
        r = _follow_bm_verify(url, r)

        if r.status_code != 200:
            return False, f"pdf_http_{r.status_code}"

        data = r.content
        if len(data) > MAX_PDF_SIZE:
            return False, "too_big"

        if not data[:4] == b"%PDF":
            head = data[:200].decode("utf-8", errors="ignore").lower()
            if "<html" in head or "<!doctype" in head:
                return False, "html_response"
            return False, "not_pdf"

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True, ""
    except Exception as e:
        return False, f"pdf_err_{type(e).__name__}"


def download_html(url: str, scraper=None) -> tuple[str | None, str]:
    """Скачивает HTML (с обработкой bm-verify)."""
    try:
        r = curl_requests.get(
            url, impersonate="chrome", timeout=HTTP_TIMEOUT,
            allow_redirects=True,
            headers={**BROWSER_HEADERS, "Referer": _referer_for(url)},
        )
        r = _follow_bm_verify(url, r)

        if r.status_code != 200:
            return None, f"html_http_{r.status_code}"
        return r.text, ""
    except Exception as e:
        return None, f"html_err_{type(e).__name__}"


def extract_pdf_text(pdf_path: Path) -> tuple[str | None, int, str]:
    try:
        doc = pymupdf.open(pdf_path)
        pages = doc.page_count
        parts = [page.get_text("text") for page in doc]
        doc.close()
        return "\n".join(parts).strip(), pages, ""
    except Exception as e:
        return None, 0, f"extract_{type(e).__name__}"


def extract_html_text(html: str) -> tuple[str | None, str]:
    """Извлекает основной текст из HTML (article, main, body)."""
    try:
        soup = BeautifulSoup(html, "lxml")
        # Удаляем мусор
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        # Приоритеты: article → main → div[role=main] → body
        node = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", attrs={"role": "main"})
            or soup.find("div", class_=lambda x: x and "article" in x.lower())
            or soup.body
        )
        if not node:
            return None, "no_body"

        # Собираем текст блоками
        parts = []
        for el in node.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = el.get_text(" ", strip=True)
            if len(text) > 30:  # отсекаем мусорные короткие строки
                parts.append(text)
        text = "\n\n".join(parts).strip()
        return text, ""
    except Exception as e:
        return None, f"html_parse_{type(e).__name__}"


def process_one(pmid: str, pdf_url: str, html_url: str | None,
                scraper=None) -> dict:
    """Пробует PDF, потом HTML. Возвращает запись индекса."""
    pdf_path = TMP_DIR / f"{pmid}.pdf"
    txt_path = TEXT_DIR / f"{pmid}.txt"

    # ── 1. PDF ────────────────────────────────────────────────
    ok, pdf_err = download_pdf(pdf_url, pdf_path, scraper)
    if ok:
        text, pages, err = extract_pdf_text(pdf_path)
        try:
            pdf_path.unlink()
        except Exception:
            pass
        if text and len(text) >= MIN_TEXT_CHARS:
            TEXT_DIR.mkdir(parents=True, exist_ok=True)
            txt_path.write_text(text, encoding="utf-8")
            return {"status": "ok", "type": "pdf", "pages": pages,
                    "chars": len(text), "source": pdf_url}
        # extract_failed → пробуем HTML
        pdf_extract_err = err or f"too_short_{len(text) if text else 0}"
    else:
        pdf_extract_err = pdf_err

    # ── 2. HTML fallback ─────────────────────────────────────
    if html_url:
        html, html_err = download_html(html_url, scraper)
        if html:
            text, err = extract_html_text(html)
            if text and len(text) >= MIN_TEXT_CHARS:
                TEXT_DIR.mkdir(parents=True, exist_ok=True)
                txt_path.write_text(text, encoding="utf-8")
                return {"status": "ok", "type": "html", "chars": len(text),
                        "source": html_url, "pdf_err": pdf_extract_err}
            html_extract_err = err or f"too_short_{len(text) if text else 0}"
        else:
            html_extract_err = html_err
    else:
        html_extract_err = "no_html_url"

    # ── 3. Всё провалилось ───────────────────────────────────
    return {"status": "failed", "pdf_error": pdf_extract_err,
            "html_error": html_extract_err, "source": pdf_url}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    unpaywall = json.loads(UNPAYWALL.read_text(encoding="utf-8"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index: dict = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}

    tasks: list[tuple[str, str, str | None]] = []
    for pmid, p in papers.items():
        doi = p.get("doi")
        if not doi:
            continue
        u = unpaywall.get(doi)
        if not u or not u.get("is_oa"):
            continue
        pdf_url = u.get("pdf")
        html_url = u.get("url")
        if not pdf_url:
            continue
        if pmid in index and index[pmid].get("status") == "ok":
            continue
        tasks.append((pmid, pdf_url, html_url))

    if args.limit:
        tasks = tasks[: args.limit]

    print(f"Всего OA с PDF: {len(tasks)}")
    print(f"Потоков:         {args.workers}")
    print(f"Кэш ok:          {sum(1 for v in index.values() if v.get('status') == 'ok')}")
    print()

    if not tasks:
        print("[OK] Нечего обрабатывать")
        return 0

    t0 = time.time()
    done = ok = err = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_one, pmid, pdf, html, None): pmid
                   for pmid, pdf, html in tasks}
        for fut in as_completed(futures):
            pmid = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": "fatal", "error": str(e)}
            index[pmid] = result
            done += 1
            if result.get("status") == "ok":
                ok += 1
            else:
                err += 1

            if done % 50 == 0:
                INDEX.write_text(
                    json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(tasks) - done) / rate if rate else 0
                print(f"[{done}/{len(tasks)}] ok={ok} err={err} · "
                      f"{rate:.2f} files/s · ETA {eta/60:.1f} мин")

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for v in index.values() if v.get("status") == "ok")
    print(f"\n[OK] {INDEX}")
    print(f"     Всего: {len(index)}, Успешно: {n_ok} ({n_ok/len(index)*100:.1f}%)")
    print(f"     Время: {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())