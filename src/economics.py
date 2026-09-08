"""Экономика: цена месяца, ценовые категории, расчёт экономии."""
import pandas as pd


def add_month_price(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    prices["цена_мес"] = (prices["цена_упаковки"] / prices["единиц_в_упаковке"]
                          * prices["норма_мес"]).round(0)
    sus = prices[prices["цена_мес"] > 5000]
    if len(sus):
        print("⚠️ Подозрительно дорогие — проверь фасовку:")
        print(sus[["добавка", "продукт", "единиц_в_упаковке", "цена_мес"]])
    return prices


def add_categories(prices: pd.DataFrame, min_offers: int = 3) -> pd.DataFrame:
    prices = prices.copy()
    prices["категория"] = prices.groupby("добавка")["цена_мес"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3,
                          labels=["эконом", "средний", "премиум"])
        if len(s) >= min_offers else "средний")
    return prices


def tier_table(prices: pd.DataFrame) -> pd.DataFrame:
    tier = (prices.pivot_table(index="добавка", columns="категория",
                               values="цена_мес", aggfunc="median").round(0))
    tier["переплата_в_раз"] = (tier["премиум"] / tier["эконом"]).round(1)
    return tier.sort_values("переплата_в_раз", ascending=False)


def savings_summary(df: pd.DataFrame, prices: pd.DataFrame, top: int = 3):
    """Возвращает (df с ценами, топ пустышек, топ рабочих, экономию за год)."""
    med = prices.groupby("добавка")["цена_мес"].median().round(0).reset_index()
    df = df.drop(columns=["цена_мес", "цена_год"], errors="ignore") \
           .merge(med, on="добавка", how="left")
    df["цена_год"] = df["цена_мес"] * 12
    trash = df[df["вердикт"] == -1].sort_values("score", ascending=False).head(top)
    gold = df[df["вердикт"] == 1].sort_values("score", ascending=False).head(top)
    save = int(trash["цена_год"].sum() - gold["цена_год"].sum())
    return df, trash, gold, save