"""brain-25-evidence — интерактивный дашборд.

Streamlit app: 94 БАДа, 37618 papers, поиск и фильтры.

Локально: streamlit run app.py
Деплой:   https://streamlit.io/cloud → public repo → main file: app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="brain-25-evidence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent


@st.cache_data(ttl=3600)
def load_papers() -> pd.DataFrame:
    """Все 37618 papers."""
    data = json.loads((ROOT / "data" / "papers" / "papers_slim.json").read_text(encoding="utf-8"))
    rows = []
    for pmid, p in data.items():
        rows.append({
            "pmid": pmid,
            "title": p.get("title"),
            "journal": p.get("journal"),
            "year": p.get("year"),
            "doi": p.get("doi"),
            "design": p.get("design"),
            "species": p.get("species"),
            "sjr_quartile": p.get("sjr_quartile"),
            "is_retracted": bool(p.get("is_retracted")),
            "pubtype": ", ".join(p.get("pubtype") or [])[:100],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_supplements() -> pd.DataFrame:
    """94 БАДа."""
    data = json.loads((ROOT / "data" / "supplements_slim.json").read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = [{"slug": k, **v} for k, v in data.items()]
    else:
        rows = data
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_sample_sizes() -> dict:
    return json.loads((ROOT / "data" / "papers" / "sample_sizes.json").read_text(encoding="utf-8"))


def main() -> None:
    st.title("🧠 brain-25-evidence")
    st.caption("Открытая база данных о 94 добавках на основе PubMed · 37 618 papers")

    with st.spinner("Загружаю данные..."):
        papers = load_papers()
        supplements = load_supplements()

    # ===== Sidebar =====
    st.sidebar.header("Фильтры")

    years = papers["year"].dropna().astype(int)
    year_range = st.sidebar.slider(
        "Год публикации",
        int(years.min()), int(years.max()),
        (2010, int(years.max())),
    )

    designs = sorted(papers["design"].dropna().unique())
    design_filter = st.sidebar.multiselect(
        "Design", designs,
        default=["rct", "meta-analysis"] if "rct" in designs else designs[:2],
    )

    species_opts = ["human", "animal", "both", "unknown", "no_mesh"]
    species_filter = st.sidebar.multiselect(
        "Species", [s for s in species_opts if s in papers["species"].values],
        default=["human"],
    )

    quartiles = ["Q1", "Q2", "Q3", "Q4"]
    quartile_filter = st.sidebar.multiselect(
        "SCImago Quartile", quartiles,
        default=["Q1", "Q2"],
    )

    only_not_retracted = st.sidebar.checkbox("Только не отозванные", value=True)

    # ===== Применяем фильтры =====
    f = papers[
        papers["year"].between(*year_range)
    ]
    if design_filter:
        f = f[f["design"].isin(design_filter)]
    if species_filter:
        f = f[f["species"].isin(species_filter)]
    if quartile_filter:
        f = f[f["sjr_quartile"].isin(quartile_filter)]
    if only_not_retracted:
        f = f[f["is_retracted"].fillna(False).astype(bool) != True]

    # ===== Метрики =====
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers", f"{len(f):,}")
    c2.metric("Журналов", f["journal"].nunique())
    c3.metric("Медианный год", int(f["year"].median()) if len(f) else "—")
    c4.metric("Q1 доля", f"{ (f['sjr_quartile'] == 'Q1').mean() * 100:.1f}%" if len(f) else "—")

    st.divider()

    # ===== Графики =====
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Papers по годам")
        by_year = f.groupby("year").size().reset_index(name="papers")
        st.line_chart(by_year, x="year", y="papers", height=280)

    with col2:
        st.subheader("Топ-15 журналов")
        top_j = f["journal"].value_counts().head(15)
        st.bar_chart(top_j, height=280)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Распределение по species")
        sp = f["species"].value_counts()
        st.bar_chart(sp, height=280)

    with col4:
        st.subheader("Распределение по design")
        d = f["design"].value_counts()
        st.bar_chart(d, height=280)

    st.divider()

    # ===== Таблица =====
    st.subheader(f"Papers ({len(f):,})")

    search = st.text_input("Поиск по title", "")

    show = f.copy()
    if search:
        mask = show["title"].str.contains(search, case=False, na=False)
        show = show[mask]

    st.dataframe(
        show[["pmid", "year", "journal", "design", "species",
              "sjr_quartile", "is_retracted", "title"]],
        use_container_width=True,
        height=400,
    )

    # ===== Экспорт =====
    csv = show.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Скачать CSV",
        csv,
        file_name="brain25_filtered.csv",
        mime="text/csv",
    )

    # ===== БАДы =====
    with st.expander("🔬 94 добавки — сырые данные"):
        st.dataframe(supplements, use_container_width=True)


if __name__ == "__main__":
    main()