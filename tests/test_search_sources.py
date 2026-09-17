"""Unit-тесты для чистых функций scripts/search_sources.py."""
from scripts.search_sources import (
    EXCLUDE_TERMS,
    MANUAL_PMIDS,
    PUBMED_QUERIES,
    TITLE_TERMS,
    _safe_year,
    _term_pattern,
    _title_excluded,
    _title_matches,
    resolve_manual,
    resolve_query,
)


# --- resolve_query ---

def test_resolve_query_russian():
    r = resolve_query("Гинкго")
    assert r is not None
    assert r == ("Гинкго", PUBMED_QUERIES["Гинкго"])


def test_resolve_query_alias_zinc():
    r = resolve_query("zinc")
    assert r is not None and r[0] == "Цинк"


def test_resolve_query_alias_ginkgo():
    r = resolve_query("ginkgo")
    assert r is not None and r[0] == "Гинкго"


def test_resolve_query_case_insensitive():
    r = resolve_query("ГИНКГО")
    assert r is not None and r[0] == "Гинкго"


def test_resolve_query_unknown():
    assert resolve_query("НесуществующееВещество") is None


def test_resolve_query_empty():
    assert resolve_query("") is None
    assert resolve_query(None) is None


# --- resolve_manual ---

def test_resolve_manual_russian():
    r = resolve_manual("Гинкго")
    assert r is not None
    assert r[1] == MANUAL_PMIDS["Гинкго"]


def test_resolve_manual_alias():
    r = resolve_manual("zinc")
    assert r is not None and r[0] == "Цинк"


def test_resolve_manual_unknown():
    assert resolve_manual("НетТакого") is None


# --- _title_matches: word-boundary + опциональная s ---

def test_title_matches_glycine_not_match_methyl():
    """glycine не должен ловить N-methylglycine."""
    assert _title_matches("N-methylglycine study", ("glycine",)) is False
    assert _title_matches("glycine administration", ("glycine",)) is True


def test_title_matches_plural():
    """s? в конце терма: duckling матчит ducklings."""
    assert _title_matches("Effects on ducklings", ("duckling",)) is True


def test_title_matches_ginkgo_both_forms():
    """В TITLE_TERMS['Гинкго'] есть оба варианта: 'egb 761' и 'egb-761'."""
    terms = TITLE_TERMS["Гинкго"]
    assert _title_matches("EGb 761 study", terms) is True
    assert _title_matches("EGB-761 trial", terms) is True


def test_title_matches_empty_terms():
    assert _title_matches("anything", ()) is False


# --- _title_excluded ---

def test_title_excluded_animals():
    assert _title_excluded("Effects on dairy cows") is True
    assert _title_excluded("Studied in rats") is True


def test_title_excluded_soy():
    """Glycine max — род сои, не БАД."""
    assert _title_excluded("Glycine max extract") is True


def test_title_excluded_human():
    assert _title_excluded("Human randomized trial") is False


# --- _safe_year ---

def test_safe_year_valid():
    assert _safe_year("2024 Jan") == 2024
    assert _safe_year("2024") == 2024
    assert _safe_year("1999 Dec-Feb") == 1999


def test_safe_year_invalid():
    assert _safe_year("?") == 0
    assert _safe_year("") == 0
    assert _safe_year(None) == 0
    assert _safe_year("abcd") == 0


# --- Sanity для словарей ---

def test_manual_pmids_nonempty():
    assert len(MANUAL_PMIDS) >= 10, "должно быть минимум 10 curated-карточек"
    for cid, pmids in MANUAL_PMIDS.items():
        assert isinstance(pmids, list) and pmids, f"{cid}: пустой список"
        for p in pmids:
            assert isinstance(p, str) and p.isdigit(), f"{cid}: плохой PMID {p!r}"


def test_manual_pmids_keys_resolvable():
    """Каждый ключ MANUAL_PMIDS должен резолвиться через resolve_query."""
    for cid in MANUAL_PMIDS:
        assert resolve_query(cid) is not None, f"{cid}: нет в PUBMED_QUERIES/ALIASES"


def test_title_terms_cover_manual_pmids():
    """У каждой curated-карточки должны быть TITLE_TERMS (для auto-пути)."""
    for cid in MANUAL_PMIDS:
        assert cid in TITLE_TERMS, f"{cid}: нет TITLE_TERMS"


def test_exclude_terms_present():
    assert "cattle" in EXCLUDE_TERMS
    assert "glycine max" in EXCLUDE_TERMS
