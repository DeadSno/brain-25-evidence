"""Граф связей между добавками.

Узлы: 130 добавок
Рёбра:
  interaction — прямое взаимодействие (из interactions)
  mech        — общий механизм
  tag         — общий тег эффекта

Метрики: degree, betweenness, closeness, eigenvector, communities (Louvain)

Вывод:
  reports/graph_stats.json        — метрики
  reports/graph_interactions.html — PyVis
  reports/graph_interactions.gexf — для Gephi

Запуск:
    python scripts/graph_interactions.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities
from pyvis.network import Network

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
OUT_DIR = ROOT / "reports"


def load_data() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def build_graph(cards: list[dict]) -> nx.Graph:
    """Граф: interactions + effect_tags + биологические маркеры в mechs."""
    G = nx.Graph()

    # 1. Узлы
    for c in cards:
        G.add_node(
            c["id"],
            grade=c.get("grade", "?"),
            category=c.get("category", "?"),
            scienceIndex=c.get("scienceIndex", 0),
        )

    # 2. Прямые interactions
    n_int = 0
    for c in cards:
        cid = c["id"]
        for inter in c.get("interactions", []):
            other = inter.get("with")
            if not other or other == "нет данных":
                continue
            if G.has_node(other):
                G.add_edge(cid, other, type="interaction",
                           severity=inter.get("severity", "low"))
                n_int += 1

    # 3. effect_tags.json — главный источник
    tags_path = ROOT / "docs" / "effect_tags.json"
    tags_data = json.loads(tags_path.read_text(encoding="utf-8"))

    tag_freq = Counter()
    for cid, tags in tags_data.items():
        for t in tags:
            tag_freq[t] += 1

    # Оставляем теги 3-50 карточек (уникальные и поголовные отсекаем)
    valid_tags = {t for t, f in tag_freq.items() if 3 <= f <= 50}

    tag_to_supps: dict[str, list[str]] = defaultdict(list)
    for cid, tags in tags_data.items():
        if not G.has_node(cid):
            continue
        for t in tags:
            if t in valid_tags:
                tag_to_supps[t].append(cid)

    n_tag_edges = 0
    for tag, supps in tag_to_supps.items():
        for i, a in enumerate(supps):
            for b in supps[i + 1:]:
                if G.has_edge(a, b):
                    # Усиливаем: +1 к весу
                    G[a][b]["weight"] = G[a][b].get("weight", 1) + 1
                    G[a][b]["shared_tags"] = G[a][b].get("shared_tags", []) + [tag]
                else:
                    G.add_edge(a, b, type="tag", shared_tags=[tag], weight=1)
                    n_tag_edges += 1

    # 4. Mechs через биологические маркеры
    BIO_KEYWORDS = [
        "серотонин", "дофамин", "габа", "гамк", "глутамат", "ацетилхолин",
        "норадреналин", "атф", "митохондри", "воспален", "оксидативн",
        "нейропротект", "нейропласт", "bdnf", "ngf", "кортизол",
        "кальци", "железо", "цинк", "vdr", "мелатонин", "аденозин",
        "циркадн", "микробиот", "кишечник", "иммунн", "nf-kb", "mtor",
        "ampk", "сиртуин", "теломераз", "инсулин", "глюкоз", "липид",
        "холестерин", "триглицерид", "антиоксидант",
    ]

    mech_to_supps: dict[str, list[str]] = defaultdict(list)
    for c in cards:
        cid = c["id"]
        text = " ".join(
            (m[0] if m else "").lower()
            for m in c.get("mechs", [])
        )
        for kw in BIO_KEYWORDS:
            if kw in text:
                mech_to_supps[kw].append(cid)

    n_mech_edges = 0
    for kw, supps in mech_to_supps.items():
        if len(supps) < 3 or len(supps) > 40:
            continue
        for i, a in enumerate(supps):
            for b in supps[i + 1:]:
                if not G.has_edge(a, b):
                    G.add_edge(a, b, type="mech", mech=kw)
                    n_mech_edges += 1

    print(f"  interactions: {n_int}")
    print(f"  tag edges:    {n_tag_edges}")
    print(f"  mech edges:   {n_mech_edges}")
    print(f"  Итого:        {G.number_of_edges()}")

    return G


def compute_metrics(G: nx.Graph) -> dict:
    """Метрики: degree, betweenness, closeness, eigenvector, Louvain."""
    print(f"\nУзлов: {G.number_of_nodes()}")
    print(f"Рёбер: {G.number_of_edges()}\n")

    degree = dict(G.degree())

    print("Считаю betweenness (10-30 сек)...")
    betweenness = nx.betweenness_centrality(G, k=min(50, G.number_of_nodes()))

    closeness = nx.closeness_centrality(G)

    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {n: 0.0 for n in G.nodes()}

    print("Ищу communities (Louvain)...")
    communities = louvain_communities(G, seed=42)
    node_to_community = {}
    for i, comm in enumerate(communities):
        for node in comm:
            node_to_community[node] = i

    top_degree = sorted(degree.items(), key=lambda x: -x[1])[:10]
    top_betweenness = sorted(betweenness.items(), key=lambda x: -x[1])[:10]
    top_eigenvector = sorted(eigenvector.items(), key=lambda x: -x[1])[:10]

    comm_sizes = Counter(node_to_community.values())
    comm_top = {}
    for cid in comm_sizes:
        members = [n for n, c in node_to_community.items() if c == cid]
        members_sorted = sorted(members, key=lambda n: -degree.get(n, 0))
        comm_top[cid] = members_sorted[:5]

    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "top_degree": top_degree,
        "top_betweenness": top_betweenness,
        "top_eigenvector": top_eigenvector,
        "n_communities": len(communities),
        "community_sizes": dict(comm_sizes),
        "community_top_members": comm_top,
        "node_to_community": node_to_community,
    }


def visualize(G: nx.Graph, node_to_community: dict, out_path: Path) -> None:
    """Интерактивный PyVis."""
    net = Network(height="800px", width="100%", bgcolor="#222",
                  font_color="white", notebook=False)
    net.barnes_hut()

    palette = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12",
               "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]

    for node in G.nodes():
        cid = node_to_community.get(node, 0)
        color = palette[cid % len(palette)]
        grade = G.nodes[node].get("grade", "?")
        size = 10 + min(G.degree(node) * 2, 40)
        title = f"{node}<br>Grade: {grade}<br>Связей: {G.degree(node)}"
        net.add_node(node, label=node, color=color, size=size, title=title)

    for a, b, attrs in G.edges(data=True):
        et = attrs.get("type", "?")
        w = attrs.get("weight", 1)
        if et == "interaction":
            width, color = 3, "#e74c3c"
            title = f"interaction ({attrs.get('severity', '?')})"
        elif et == "mech":
            width, color = 2, "#3498db"
            title = f"механизм: {attrs.get('mech', '?')}"
        else:  # tag
            width = 1 + w * 0.5
            color = "#2ecc71"
            title = f"теги: {', '.join(attrs.get('shared_tags', []))}"
        net.add_edge(a, b, width=width, color=color, title=title)

    net.write_html(str(out_path), open_browser=False, notebook=False)


def main() -> int:
    print("Загружаю data.json...")
    cards = load_data()
    print(f"Карточек: {len(cards)}")

    print("\nСтрою граф...")
    G = build_graph(cards)

    stats = compute_metrics(G)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats_out = {k: v for k, v in stats.items() if k != "node_to_community"}
    (OUT_DIR / "graph_stats.json").write_text(
        json.dumps(stats_out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # GEXF не умеет list в атрибутах — превращаем в строки
    G_gexf = G.copy()
    for a, b, attrs in G_gexf.edges(data=True):
        if "shared_tags" in attrs and isinstance(attrs["shared_tags"], list):
            attrs["shared_tags"] = ",".join(attrs["shared_tags"])
    nx.write_gexf(G_gexf, OUT_DIR / "graph_interactions.gexf")

    print("\nСтрою визуализацию PyVis...")
    visualize(G, stats["node_to_community"],
              OUT_DIR / "graph_interactions.html")

    print(f"\n=== Метрики графа ===")
    print(f"Узлов:      {stats['n_nodes']}")
    print(f"Рёбер:      {stats['n_edges']}")
    print(f"Сообществ:  {stats['n_communities']}")
    print()
    print("Топ-10 Degree (популярность):")
    for name, val in stats["top_degree"]:
        print(f"  {val:>4}  {name}")
    print()
    print("Топ-10 Betweenness (мосты):")
    for name, val in stats["top_betweenness"]:
        print(f"  {val:.3f}  {name}")
    print()
    print("Сообщества:")
    for cid, members in sorted(stats["community_top_members"].items()):
        size = stats["community_sizes"].get(cid, 0)
        print(f"  Кластер {cid} ({size} узлов): {', '.join(members)}")

    print(f"\n[OK] reports/graph_stats.json")
    print(f"[OK] reports/graph_interactions.html")
    print(f"[OK] reports/graph_interactions.gexf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())