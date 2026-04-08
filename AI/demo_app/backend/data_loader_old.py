from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data_sources"


def load_csv(relative_path: str) -> pd.DataFrame:
    path = DATA_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")
    return pd.read_csv(path)


def load_all() -> Dict[str, pd.DataFrame]:
    return {
        "sales": load_csv("sales_data/raw/sales.csv"),
        "festivals": load_csv("festivals/raw/festivals.csv"),
        "climate": load_csv("climate/raw/weather.csv"),
        "competitor_prices": load_csv("competitor_prices/raw/competitor_prices.csv"),
        "reviews": load_csv("customer_reviews/raw/reviews.csv"),
        "geopolitical": load_csv("geopolitical/raw/events.csv"),
    }
