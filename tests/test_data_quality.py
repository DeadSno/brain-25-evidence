from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
EXPECTED_WB = {"добавка", "продукт", "единиц_в_упаковке", "цена_упаковки",
               "норма_мес", "источник", "дата", "цена_мес", "категория"}


def test_wb_schema():
    wb = pd.read_excel(RAW / "prices_wb.xlsx")
    assert EXPECTED_WB <= set(wb.columns)


def test_wb_ranges_and_coverage():
    wb = pd.read_excel(RAW / "prices_wb.xlsx")
    assert len(wb) >= 75
    assert wb["цена_мес"].between(50, 10000).all()
    assert (wb.groupby("добавка").size() >= 3).all()


def test_processed_ok():
    df = pd.read_csv(PROC / "evidence_scored.csv")
    assert {"добавка", "score", "вердикт", "цена_мес"} <= set(df.columns)
    assert len(df) == 25


def test_freshness():
    wb = pd.read_excel(RAW / "prices_wb.xlsx")
    d = pd.to_datetime(wb["дата"]).max()
    assert (pd.Timestamp.today() - d).days <= 120, "цены устарели — обнови!"