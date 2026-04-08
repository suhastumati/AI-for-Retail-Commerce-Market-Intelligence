from __future__ import annotations

from datetime import datetime
from typing import Tuple

import numpy as np
import pandas as pd


def _month_key(dt: pd.Timestamp) -> str:
    return dt.strftime("%Y-%m")


def forecast_monthly_demand(
    sales: pd.DataFrame,
    festivals: pd.DataFrame,
    sku: str,
    as_of: datetime | None = None,
) -> Tuple[int, float, list[str]]:
    sales = sales.copy()
    sales["date"] = pd.to_datetime(sales["date"])
    if as_of is None:
        as_of = sales["date"].max().to_pydatetime()

    sku_sales = sales[sales["sku"] == sku].sort_values("date")
    if sku_sales.empty:
        return 0, 0.3, ["Insufficient sales history"]

    recent = sku_sales.tail(12)
    base_demand = recent["units_sold"].mean()

    next_month = (pd.Timestamp(as_of) + pd.offsets.MonthBegin(1)).to_pydatetime()
    next_month_key = next_month.strftime("%Y-%m")

    festivals = festivals.copy()
    festivals["date"] = pd.to_datetime(festivals["date"])
    festivals["month_key"] = festivals["date"].apply(_month_key)

    uplift_factor = 1.0
    driver_notes = []
    month_festivals = festivals[festivals["month_key"] == next_month_key]
    if not month_festivals.empty:
        uplift = month_festivals["impact_factor"].mean()
        uplift_factor += uplift
        names = ", ".join(month_festivals["festival"].unique().tolist())
        driver_notes.append(f"Festival uplift expected: {names}")

    forecast = max(1, int(base_demand * uplift_factor))
    volatility = recent["units_sold"].std() if len(recent) > 1 else 0.0
    confidence = float(max(0.4, min(0.9, 1 - (volatility / (base_demand + 1)))))

    if not driver_notes:
        driver_notes.append("Seasonality based on last 12 months")

    return forecast, confidence, driver_notes
