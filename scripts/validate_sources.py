"""Периодическая валидация key_sources в docs/data.json через PubMed esummary.

Использование:
    python scripts/validate_sources.py              # проверить сейчас
    python scripts/validate_sources.py --quarterly  # пропустить, если <90 дней с прошлого раза
    python scripts/validate_sources.py --force      # игнорировать marker

Marker:  reports/.last_validation       — timestamp + итоги последнего прогона
Отчёт:   reports/validation_report.json — детально по каждому PMID

Автоматизация (Windows Task Scheduler):
    ежедневный триггер + флаг --quarterly. Скрипт сам решит, пора ли.
    Если машина была выключена в «день квартала» — следующий запуск отработает.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
MARKER = ROOT / "reports" / ".last_validation"
REPORT = ROOT / "reports" / "validation_report.json"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "brain-25-evidence/1.0"
QUARTER_DAYS = 90


def _get(url: str, retries: int = 3) -> str:
    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Failed: {url} ({last_exc})")


def _safe_year(pubdate: str | None) -> int:
    if not pubdate:
        return 0
    head = str(pubdate)[:4]
    return int(head) if head.isdigit() else 0


def esummary(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    raw = _get(url)
    data = json.loads(raw).get("result", {}) or {}
    out: dict[str, dict] = {}
    for pmid in pmids:
        info = data.get(pmid)
        if not isinstance(info, dict) or info.get("error"):
            continue
        out[pmid] = {
            "title": info.get("title") or "?",
            "year": _safe_year(info.get("pubdate")),
            "journal": info.get("fulljournalname") or "?",
            "pubtype": list(info.get("pubtype") or []),
        }
    return out


def _days_since(marker: Path) -> float | None:
    if not marker.exists():
        return None
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(payload["timestamp"])
    except Exception:
        return None
    return (datetime.now(timezone.utc) - ts).total_seconds() / 86400


def _write_marker(summary: dict) -> None:
    MARKER.parent.mkdir(exist_ok=True)
    MARKER.write_text(
        json.dumps(
            {"timestamp": datetime.now(timezone.utc).isoformat(), **summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка key_sources в data.json")
    parser.add_argument("--quarterly", action="store_true",
                        help=f"запускать только если с прошлого раза >{QUARTER_DAYS} дней")
    parser.add_argument("--force", action="store_true",
                        help="игнорировать marker и проверить сейчас")
    args = parser.parse_args()

    if args.quarterly and not args.force:
        days = _days_since(MARKER)
        if days is not None and days < QUARTER_DAYS:
            print(f"[skip] Последняя проверка {days:.1f} дн. назад "
                  f"(< {QUARTER_DAYS}). Используйте --force для принудительного запуска.")
            return 0
        if days is not None:
            print(f"[quarterly] Прошло {days:.1f} дн. — запускаем проверку.")

    if not DATA_JSON.exists():
        print(f"[!] нет {DATA_JSON}", file=sys.stderr)
        return 1

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    cards = [c for c in data if c.get("key_sources")]
    if not cards:
        print("[!] Ни в одной карточке нет key_sources. Сначала apply_sources.py.",
              file=sys.stderr)
        return 1

    print(f"Проверяю {len(cards)} карточек...\n")

    report: dict = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "cards": {},
        "totals": {},
    }
    n_ok = n_missing = n_changed = 0

    for card in cards:
        cid = card["id"]
        stored = card["key_sources"]
        pmids = [s["pmid"] for s in stored]
        try:
            live = esummary(pmids)
        except Exception as e:  # noqa: BLE001
            print(f"— {cid}: [!] {e}", file=sys.stderr)
            report["cards"][cid] = {"status": "error", "error": str(e)}
            continue

        print(f"— {cid}")
        card_report: dict = {"pmids": {}, "status": "ok"}

        for s in stored:
            pid = s["pmid"]
            info = live.get(pid)
            if not info:
                n_missing += 1
                print(f"    [MISSING] {pid}: не найден в PubMed")
                card_report["pmids"][pid] = {"status": "missing"}
                card_report["status"] = "issues"
                continue

            diffs: list[str] = []
            if s.get("year") != info["year"]:
                diffs.append(f"year: {s.get('year')} → {info['year']}")
            if s.get("title") != info["title"]:
                diffs.append("title изменился")
            if sorted(s.get("pubtype") or []) != sorted(info["pubtype"]):
                diffs.append(
                    f"pubtype: [{', '.join(s.get('pubtype') or [])}] → "
                    f"[{', '.join(info['pubtype'])}]"
                )
            if s.get("journal") != info["journal"]:
                diffs.append("journal изменился")

            if diffs:
                n_changed += 1
                print(f"    [CHANGED] {pid}: {'; '.join(diffs)}")
                card_report["pmids"][pid] = {
                    "status": "changed",
                    "diffs": diffs,
                    "stored": {k: s.get(k) for k in ("title", "year", "journal", "pubtype")},
                    "live": info,
                }
                card_report["status"] = "issues"
            else:
                n_ok += 1
                print(f"    [OK]      {pid}")
                card_report["pmids"][pid] = {"status": "ok"}

        report["cards"][cid] = card_report

    report["totals"] = {"ok": n_ok, "changed": n_changed, "missing": n_missing}

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    print(f"\nИтого: {n_ok} OK, {n_changed} changed, {n_missing} missing")
    print(f"[OK] Отчёт: {REPORT}")

    _write_marker({"ok": n_ok, "changed": n_changed, "missing": n_missing})
    print(f"[OK] Marker обновлён: {MARKER}")
    return 0 if (n_missing == 0 and n_changed == 0) else 2


if __name__ == "__main__":
    sys.exit(main())