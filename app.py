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

    st.divider()

    # ===== 💰 ФИНАНСИРОВАНИЕ =====
    st.header("💰 Кто финансирует исследования")
    st.caption("Данные из Europe PMC (JATS XML) + CrossRef. Из 5 059 полных текстов 1 342 указывают funding.")

    try:
        funders_csv = pd.read_csv(ROOT / "data" / "processed" / "funders_top.csv")
        countries_csv = pd.read_csv(ROOT / "data" / "processed" / "countries_top.csv")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Всего статей (XML)", "5 059")
        c2.metric("С финансированием", "1 342", "26.5%")
        c3.metric("С COI", "341", "6.7%")
        c4.metric("Китай vs США", "4.51×", "госфонды")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Топ-15 фондов")
            top_f = funders_csv.head(15).set_index("funder")["papers"]
            st.bar_chart(top_f, height=400)

        with col2:
            st.subheader("Топ-20 стран (по affiliations)")
            top_c = countries_csv.head(20).set_index("country")["papers"]
            st.bar_chart(top_c, height=400)

        # Funding rate по годам — данные из reports
        st.subheader("📈 Доля статей с указанным финансированием")
        funding_by_year = pd.DataFrame({
            "year":  [2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026],
            "rate":  [17.8,17.4,22.9,18.4,27.8,28.6,23.7,26.1,22.7,14.1,12.4,14.9,27.8,37.1,32.0,33.6,34.6],
            "total": [45,46,70,103,108,133,152,188,233,269,396,450,553,456,596,654,540],
        }).set_index("year")
        st.line_chart(funding_by_year["rate"], height=250)

        st.caption("📊 Источник: Europe PMC REST · [funders_top.csv](https://github.com/DeadSno/brain-25-evidence/blob/main/data/processed/funders_top.csv)")
    except FileNotFoundError:
        st.warning("Файлы funders_top.csv не найдены. Запусти `python scripts/build_funders_index.py`")


if __name__ == "__main__":
    main()