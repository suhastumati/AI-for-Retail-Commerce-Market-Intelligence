from __future__ import annotations

import math
import random
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data_sources"

random.seed(42)

SKUS = [
    {
        "sku": "TV-IND-001",
        "product": 'Smart TV 55"',
        "brand": "BlueBrand",
        "base_price": 42000,
        "base_cost": 30000,
    },
    {
        "sku": "MB-IND-002",
        "product": "Smartphone Pro",
        "brand": "BlueBrand",
        "base_price": 52000,
        "base_cost": 36000,
    },
]


def month_range(start: str, end: str) -> list[datetime]:
    start_dt = datetime.strptime(start, "%Y-%m")
    end_dt = datetime.strptime(end, "%Y-%m")
    months = []
    current = start_dt
    while current <= end_dt:
        months.append(current)
        year = current.year + (current.month // 12)
        month = current.month % 12 + 1
        current = current.replace(year=year, month=month)
    return months


def festival_factor(month: int) -> float:
    if month in (10, 11):
        return 1.35
    if month == 3:
        return 1.15
    if month == 8:
        return 1.1
    return 1.0


def generate_sales() -> pd.DataFrame:
    rows = []
    months = month_range("2019-01", "2024-12")
    for sku_meta in SKUS:
        for dt in months:
            season = 1.0 + 0.15 * math.sin((dt.month / 12) * math.pi * 2)
            fest = festival_factor(dt.month)
            price = sku_meta["base_price"] * random.uniform(0.92, 1.08)
            cost = sku_meta["base_cost"] * random.uniform(0.95, 1.05)
            base_units = 900 if sku_meta["sku"].startswith("TV") else 1200
            units = int(base_units * season * fest * random.uniform(0.85, 1.15))
            rows.append(
                {
                    "date": dt.strftime("%Y-%m-%d"),
                    "sku": sku_meta["sku"],
                    "product": sku_meta["product"],
                    "brand": sku_meta["brand"],
                    "price": round(price, 2),
                    "cost": round(cost, 2),
                    "units_sold": units,
                    "region": "India",
                }
            )
    return pd.DataFrame(rows)


def generate_festivals() -> pd.DataFrame:
    rows = []
    for year in range(2019, 2026):
        rows.extend(
            [
                {"date": f"{year}-03-01", "festival": "Holi", "impact_factor": 0.15},
                {"date": f"{year}-08-01", "festival": "Onam", "impact_factor": 0.1},
                {"date": f"{year}-10-15", "festival": "Diwali", "impact_factor": 0.35},
                {"date": f"{year}-11-01", "festival": "Diwali", "impact_factor": 0.35},
            ]
        )
    return pd.DataFrame(rows)


def generate_weather() -> pd.DataFrame:
    rows = []
    months = month_range("2019-01", "2024-12")
    for dt in months:
        temp = 20 + 12 * math.sin((dt.month / 12) * math.pi * 2)
        rainfall = 60 + 40 * math.sin((dt.month / 12) * math.pi * 2 + 1.1)
        rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "region": "India",
                "avg_temp_c": round(temp, 1),
                "rainfall_mm": round(rainfall, 1),
            }
        )
    return pd.DataFrame(rows)


def generate_competitor_prices() -> pd.DataFrame:
    rows = []
    months = month_range("2021-01", "2024-12")
    for sku_meta in SKUS:
        for dt in months:
            for competitor in ("CompeteX", "MarketHub"):
                comp_price = sku_meta["base_price"] * random.uniform(0.9, 1.1)
                rows.append(
                    {
                        "date": dt.strftime("%Y-%m-%d"),
                        "sku": sku_meta["sku"],
                        "competitor": competitor,
                        "price": round(comp_price, 2),
                    }
                )
    return pd.DataFrame(rows)


def generate_reviews() -> pd.DataFrame:
    rows = []
    for sku_meta in SKUS:
        for idx in range(120):
            rating = random.choice([3, 4, 4, 5, 5]) if sku_meta["sku"].startswith("TV") else random.choice([2, 3, 4, 5])
            text = "Great value and smooth performance" if rating >= 4 else "Battery issue and slow response"
            rows.append(
                {
                    "date": f"2024-12-{(idx % 28) + 1:02d}",
                    "sku": sku_meta["sku"],
                    "rating": rating,
                    "review_text": text,
                }
            )
    return pd.DataFrame(rows)


def generate_geopolitical() -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        rows.append(
            {
                "date": f"2024-{month:02d}-15",
                "region": "India",
                "event_type": "SupplyChain",
                "impact_score": round(random.uniform(0.1, 0.4), 2),
                "summary": "Logistics delays in key ports",
            }
        )
    return pd.DataFrame(rows)


def write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> None:
    write(generate_sales(), DATA_DIR / "sales_data/raw/sales.csv")
    write(generate_festivals(), DATA_DIR / "festivals/raw/festivals.csv")
    write(generate_weather(), DATA_DIR / "climate/raw/weather.csv")
    write(generate_competitor_prices(), DATA_DIR / "competitor_prices/raw/competitor_prices.csv")
    write(generate_reviews(), DATA_DIR / "customer_reviews/raw/reviews.csv")
    write(generate_geopolitical(), DATA_DIR / "geopolitical/raw/events.csv")


if __name__ == "__main__":
    main()
