"""Графики трендов: публикации PubMed и Wikipedia-популярность.

Читает data/timeseries/{pubmed,wiki}.json, строит 3 графика:
  1. Топ-15 добавок по росту публикаций (2015-2025)
  2. Wikipedia-популярность топ-5
  3. Публикации vs Wikipedia (scatter)

Сохраняет: reports/trends.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # без GUI
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUBMED = ROOT / "data" / "timeseries" / "pubmed.json"
WIKI = ROOT / "data" / "timeseries" / "wiki.json"
CITATIONS = ROOT / "data" / "timeseries" / "citations.json"
DATA = ROOT / "docs" / "data.json"
OUT = ROOT / "reports" / "trends.png"

# Тёмная тема сайта
BG = "#1c1c1e"
FG = "#e9eaee"
GRID = "#3a3f48"
COLORS = {"A": "#22c55e", "B": "#84cc16", "C": "#f59e0b", "D": "#ef4444"}

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "axes.edgecolor": GRID,
    "axes.labelcolor": FG,
    "text.color": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "grid.color": GRID,
    "grid.alpha": 0.4,
    "font.size": 9,
    "font.family": "DejaVu Sans",
})


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def grade_of(cid: str, data: list[dict]) -> str:
    for c in data:
        if c["id"] == cid:
            return c.get("grade", "C")
    return "C"


def calc_growth(series: dict[str, int], first_years: int = 3, last_years: int = 3) -> float:
    """Рост = среднее за последние N лет / среднее за первые N лет."""
    years = sorted(series.keys())
    if len(years) < first_years + last_years:
        return 0.0
    first = np.mean([series[y] for y in years[:first_years]])
    last = np.mean([series[y] for y in years[-last_years:]])
    return (last / first) if first > 0 else 0.0


def plot_top_growth(ax, pubmed: dict, data: list[dict]) -> None:
    """Топ-15 по росту публикаций."""
    growth = {cid: calc_growth(series) for cid, series in pubmed.items()}
    # Фильтр: только с базой ≥20 публикаций в первые годы (иначе шум)
    filtered = {
        cid: g for cid, g in growth.items()
        if g > 1.05 and np.mean([pubmed[cid][y] for y in sorted(pubmed[cid])[:3]]) >= 20
    }
    top = sorted(filtered.items(), key=lambda x: -x[1])[:15]
    names = [t[0] for t in top]
    values = [t[1] for t in top]
    colors = [COLORS.get(grade_of(n, data), "#888") for n in names]

    y_pos = np.arange(len(names))
    ax.barh(y_pos, values, color=colors, alpha=0.85)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Рост публикаций (× к базе 2015-2017)", color=FG)
    ax.set_title("Топ-15 добавок по росту публикаций 2015→2025", color=FG, fontsize=11)
    ax.grid(True, axis="x", alpha=0.3)
    ax.axvline(1.0, color=GRID, linestyle="--", alpha=0.5)
    for i, v in enumerate(values):
        ax.text(v + 0.02, i, f"{v:.2f}×", va="center", fontsize=8, color=FG)


def plot_wiki_top(ax, wiki: dict, data: list[dict]) -> None:
    """Wikipedia-популярность топ-5 (по последнему месяцу)."""
    # Топ-5 по последнему значению
    last_month = {}
    for cid, series in wiki.items():
        if not series:
            continue
        months = sorted(series.keys())
        last_month[cid] = series[months[-1]]
    top5 = sorted(last_month.items(), key=lambda x: -x[1])[:5]
    names = [t[0] for t in top5]

    for name in names:
        series = wiki[name]
        months = sorted(series.keys())
        # Скользящее среднее 3 мес для гладкости
        vals = np.array([series[m] for m in months], dtype=float)
        if len(vals) >= 3:
            smooth = np.convolve(vals, np.ones(3) / 3, mode="valid")
            xs = months[2:]
        else:
            smooth, xs = vals, months
        grade = grade_of(name, data)
        ax.plot(xs, smooth, label=name, color=COLORS.get(grade, "#888"), linewidth=1.4)

    # Показываем каждые 12 месяцев
    tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
    ax.set_xticks([months[i] for i in tick_positions])
    ax.set_xticklabels([months[i][:4] for i in tick_positions], rotation=0, fontsize=8)
    ax.set_ylabel("Просмотры ru.wikipedia / мес", color=FG)
    ax.set_title("Wikipedia-популярность топ-5 добавок", color=FG, fontsize=11)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.3)
    ax.grid(True, alpha=0.3)


def plot_scatter(ax, pubmed: dict, wiki: dict, data: list[dict]) -> None:
    """Публикации 2024 vs Wikipedia 2024-12."""
    xs, ys, colors, labels = [], [], [], []
    for cid in pubmed:
        if cid not in wiki or not wiki[cid]:
            continue
        p_2024 = pubmed[cid].get("2024") or 0
        w_series = wiki[cid]
        w_last = sorted(w_series.keys())[-1]
        w_2024 = w_series.get(w_last) or 0
        if p_2024 > 0 and w_2024 > 0:
            xs.append(p_2024)
            ys.append(w_2024)
            colors.append(COLORS.get(grade_of(cid, data), "#888"))
            labels.append(cid)

    ax.scatter(xs, ys, c=colors, alpha=0.7, s=40)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Публикации PubMed (2024)", color=FG)
    ax.set_ylabel("Просмотры Wikipedia (декабрь 2024)", color=FG)
    ax.set_title("Публикации vs Wikipedia (log-log)", color=FG, fontsize=11)
    ax.grid(True, alpha=0.3)

    # Аннотируем топ-5 по просмотрам
    if xs:
        top_idx = np.argsort(ys)[-5:]
        for i in top_idx:
            ax.annotate(labels[i], (xs[i], ys[i]), fontsize=7, alpha=0.8)


def plot_citations_total(ax, citations: dict) -> None:
    """Общая сумма цитат по всем добавкам за год — глобальный тренд."""
    years = sorted({y for s in citations.values() for y in s.keys()})
    totals = {y: sum(s.get(y, 0) for s in citations.values()) for y in years}
    values = [totals[y] for y in years]

    bars = ax.bar(years, values, color="#3498db", alpha=0.85, edgecolor="#2980b9")
    ax.set_ylabel("Цитат в год (сумма по 94)", color=FG)
    ax.set_title(
        "Общий поток цитат по всем добавкам (ключевые источники)", 
        color=FG, fontsize=11,
    )
    ax.grid(True, axis="y", alpha=0.3)

    for i, y in enumerate(years):
        ax.text(i, values[i] + max(values) * 0.015, f"{values[i]:,}",
                ha="center", fontsize=7, color=FG)


def main() -> int:
    if not PUBMED.exists():
        print(f"[ERROR] {PUBMED} не найден", file=sys.stderr)
        return 1

    pubmed = load_json(PUBMED)
    wiki = load_json(WIKI) if WIKI.exists() else {}
    citations = load_json(CITATIONS) if CITATIONS.exists() else {}
    data = load_json(DATA)

    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.25,
                          width_ratios=[1.1, 1], height_ratios=[1, 1, 1])

    ax1 = fig.add_subplot(gs[:, 0])  # левая колонка — топ-15
    ax2 = fig.add_subplot(gs[0, 1])  # верх справа — wiki
    ax3 = fig.add_subplot(gs[1, 1])  # середина — scatter
    ax4 = fig.add_subplot(gs[2, :])  # низ — цитаты (на всю ширину)

    plot_top_growth(ax1, pubmed, data)
    if wiki:
        plot_wiki_top(ax2, wiki, data)
        plot_scatter(ax3, pubmed, wiki, data)
    if citations:
        plot_citations_total(ax4, citations)

    fig.suptitle(
        "brain-25-evidence: тренды популярности добавок 2015-2025",
        fontsize=13, color=FG, y=0.98,
    )

    OUT.parent.mkdir(exist_ok=True)
    plt.savefig(OUT, dpi=120, bbox_inches="tight")
    plt.close()

    print(f"[OK] {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())