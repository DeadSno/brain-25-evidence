import pandas as pd
from src import economics


def test_add_month_price():
    p = pd.DataFrame([{"цена_упаковки": 890, "единиц_в_упаковке": 500, "норма_мес": 150}])
    assert economics.add_month_price(p)["цена_мес"].iloc[0] == 267.0


def test_categories_few_offers():
    p = pd.DataFrame([{"добавка": "X", "цена_мес": 100},
                      {"добавка": "X", "цена_мес": 200}])
    assert (economics.add_categories(p)["категория"] == "средний").all()


def test_savings():
    df = pd.DataFrame([{"добавка": "A", "вердикт": -1, "score": 10},
                       {"добавка": "B", "вердикт": 1, "score": 9}])
    p = pd.DataFrame([{"добавка": "A", "цена_мес": 100},
                      {"добавка": "B", "цена_мес": 50}])
    _, _, _, save = economics.savings_summary(df, p)
    assert save == 100 * 12 - 50 * 12