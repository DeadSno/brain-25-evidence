"""Ежедневный сбор цен WB → история для v1.3."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import parsers

df = parsers.collect_wb_prices()
if df.empty:
    raise SystemExit("WB вернул пусто — пропускаем")
f = Path("data/raw/prices_wb_history.csv")
old = pd.read_csv(f) if f.exists() else pd.DataFrame()
new = pd.concat([old, df], ignore_index=True)
new = new.drop_duplicates(subset=["дата", "добавка", "источник"])
new.to_csv(f, index=False, encoding="utf-8-sig")
print(f"history: {len(new)} строк")