from __future__ import annotations

from typing import Tuple, List

import numpy as np
import pandas as pd


def estimate_elasticity(sales: pd.DataFrame, sku: str) -> float:
    sku_sales = sales[sales["sku"] == sku].copy()
    if len(sku_sales) < 6:
        return -1.2

    sku_sales = sku_sales[sku_sales["price"] > 0]
    sku_sales = sku_sales[sku_sales["units_sold"] > 0]
    if len(sku_sales) < 6:
        return -1.2

    x = np.log(sku_sales["price"].values)
    y = np.log(sku_sales["units_sold"].values)
    slope, _ = np.polyfit(x, y, 1)
    if np.isnan(slope) or slope >= 0:
        return -1.0
    return float(slope)


def recommend_price(
    sales: pd.DataFrame,
    competitor_prices: pd.DataFrame,
    sku: str,
    base_demand: int,
) -> Tuple[float, float, float, List[str]]:
    sku_sales = sales[sales["sku"] == sku].copy()
    if sku_sales.empty:
        return 0.0, 0.0, 0.0, ["Insufficient sales history"]

    sku_sales["date"] = pd.to_datetime(sku_sales["date"])
    sku_sales = sku_sales.sort_values("date")

    current_row = sku_sales.iloc[-1]
    current_price = float(current_row["price"])
    cost = float(current_row["cost"])

    elasticity = estimate_elasticity(sku_sales, sku)

    competitor_prices = competitor_prices[competitor_prices["sku"] == sku].copy()
    competitor_price = None
    if not competitor_prices.empty:
        competitor_prices["date"] = pd.to_datetime(competitor_prices["date"])
        recent_comp = competitor_prices.sort_values("date").tail(6)
        competitor_price = float(recent_comp["price"].mean())

    min_price = max(cost * 1.02, current_price * 0.8)
    max_price = current_price * 1.2
    if competitor_price:
        max_price = min(max_price, competitor_price * 1.05)
        min_price = min_price if min_price < competitor_price * 1.1 else competitor_price * 0.95

    price_grid = np.linspace(min_price, max_price, 25)

    best_price = current_price
    best_profit = -float("inf")
    for price in price_grid:
        demand = max(1, base_demand * (price / current_price) ** elasticity)
        profit = (price - cost) * demand
        if profit > best_profit:
            best_profit = profit
            best_price = price

    discount_pct = max(0.0, (current_price - best_price) / current_price * 100)
    driver_notes = [
        f"Elasticity estimate: {elasticity:.2f}",
        f"Competitor anchor: {competitor_price:.0f}" if competitor_price else "Competitor anchor: not available",
        f"Cost floor: {cost:.0f}",
    ]

    return float(best_price), float(best_profit), float(discount_pct), driver_notes
