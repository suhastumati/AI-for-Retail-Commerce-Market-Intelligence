"""
Data loader — reads all project CSVs + real downloaded datasets + sentiment output.

Priority for each dataset:
  1. Real downloaded data (from internet / python-holidays / World Bank)
  2. Project CSV (existing curated data)
  3. Empty DataFrame (graceful fallback)
"""
from pathlib import Path
import pandas as pd

# Resolve project root (two levels up from backend/)
_HERE = Path(__file__).resolve().parent
_DATA = _HERE.parent.parent / "data_sources"
_SENT = _HERE.parent.parent / "ai_processing_layer" / "sentiment_analysis" / "outputs"

CSV_MAP = {
    "sales":       _DATA / "sales_data"         / "raw" / "sales.csv",
    "reviews":     _DATA / "customer_reviews"    / "raw" / "reviews.csv",
    "competitors": _DATA / "competitor_prices"   / "raw" / "competitor_prices.csv",
    "weather":     _DATA / "climate"             / "raw" / "weather.csv",
    "events":      _DATA / "geopolitical"        / "raw" / "events.csv",
    "festivals":   _DATA / "festivals"           / "raw" / "festivals.csv",
}

# Real downloaded datasets (preferred over synthetic CSVs)
REAL_DATA_MAP = {
    # India public holidays from python-holidays (2019-2027, 127 rows)
    "festivals": _DATA / "festivals" / "raw" / "india_holidays_real.csv",
    # GDELT India events snapshot (5000 rows, latest available)
    "gdelt":     _DATA / "geopolitical" / "raw" / "gdelt_india_20260406.csv",
    # Wikipedia pageviews for electronics brands (576 rows)
    "wiki_views": _DATA / "climate" / "wikipedia_pageviews_smartphones.csv",
    # World Bank India CPI inflation (15 years)
    "cpi":       _DATA / "climate" / "india_cpi_worldbank.csv",
    # World Bank India GDP per capita
    "gdp":       _DATA / "climate" / "india_gdp_per_capita_worldbank.csv",
}

SENTIMENT_FILE = _SENT / "final_comprehensive_analysis_v2.csv"


def _load_csv(path: Path, label: str) -> pd.DataFrame:
    """Load a CSV, parse date column, print status."""
    if not path.exists():
        print(f"  ✗  {label:20s} → MISSING  ({path.name})")
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    print(f"  ✓  {label:20s} → {len(df):>5} rows  ({path.name})")
    return df


def load_all() -> dict[str, pd.DataFrame]:
    """Load every dataset. Real downloaded data takes priority over synthetic CSVs."""
    frames: dict[str, pd.DataFrame] = {}

    # ── Core project CSVs ─────────────────────────────────────────────────────
    for name, path in CSV_MAP.items():
        if name == "festivals":
            # Prefer real holidays over synthetic festivals.csv
            real_path = REAL_DATA_MAP["festivals"]
            if real_path.exists():
                df = _load_csv(real_path, f"{name} (real)")
                # Normalise column names to match what analytics.py expects
                if "impact_factor" not in df.columns and "impact" in df.columns:
                    df = df.rename(columns={"impact": "impact_factor"})
                frames[name] = df
                continue
        frames[name] = _load_csv(path, name)

    # ── Real external datasets (loaded as extra keys) ─────────────────────────
    for name, path in REAL_DATA_MAP.items():
        if name == "festivals":
            continue  # already handled above
        if name == "gdelt":
            df = _load_csv(path, f"{name} (real)")
            if not df.empty:
                # Keep only retail-relevant columns to avoid polluting analytics
                keep_cols = [c for c in [
                    "GlobalEventID", "Day", "Actor1Name", "Actor2Name",
                    "EventRootCode", "GoldsteinScale", "NumMentions", "AvgTone",
                    "ActionGeo_FullName", "ActionGeo_CountryCode", "SOURCEURL",
                ] if c in df.columns]
                frames["gdelt"] = df[keep_cols] if keep_cols else df
        else:
            frames[name] = _load_csv(path, f"{name} (real)")

    # ── Sentiment / enriched analysis ─────────────────────────────────────────
    if SENTIMENT_FILE.exists():
        sdf = pd.read_csv(SENTIMENT_FILE)
        if "date" in sdf.columns:
            sdf["date"] = pd.to_datetime(sdf["date"], errors="coerce")
        frames["sentiment"] = sdf
        print(f"  ✓  {'sentiment':20s} → {len(sdf):>5} rows  ({SENTIMENT_FILE.name})")
    else:
        frames["sentiment"] = pd.DataFrame()
        print(f"  ✗  {'sentiment':20s} → MISSING  ({SENTIMENT_FILE})")

    return frames
