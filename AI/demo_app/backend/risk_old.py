from __future__ import annotations

from typing import List, Tuple

import pandas as pd


def market_risk(events: pd.DataFrame, region: str) -> Tuple[float, List[str]]:
    if events.empty:
        return 0.1, ["No recent geopolitical events"]

    events = events.copy()
    events["date"] = pd.to_datetime(events["date"])
    recent = events.sort_values("date").tail(20)
    region_events = recent[recent["region"].str.lower() == region.lower()]
    if region_events.empty:
        return 0.15, ["No recent regional events"]

    avg_impact = region_events["impact_score"].mean()
    risk_level = min(1.0, max(0.1, avg_impact))
    notes = region_events["summary"].head(3).tolist()
    return float(risk_level), notes
