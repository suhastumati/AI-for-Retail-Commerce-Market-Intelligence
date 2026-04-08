"""
Live Data Fetcher — Zero API Keys Required.

All sources are genuinely free and open with no authentication:

  1. GDELT Direct CSV  — http://data.gdeltproject.org/events/  (updates every 15 min)
  2. Wikipedia Pageviews API — https://wikimedia.org/api/rest_v1/ (free, no key)
  3. World Bank API    — https://api.worldbank.org/v2/ (free, no key)
  4. python-holidays   — installed package (offline, no network needed)
  5. pytrends (optional) — unofficial Google Trends (no key, rate-limited)

Results are cached in /cache/live/ to stay within respectful usage.
"""
from __future__ import annotations

import io
import json
import logging
import os
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache" / "live"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Data sources directory (where real CSVs live)
DATA_DIR = Path(__file__).parent.parent.parent / "data_sources"

HEADERS = {
    "User-Agent": "RetailIntelligenceResearch/1.0 (academic use; contact: research@bluepill.ai)",
    "Accept": "application/json, text/plain, */*",
}

# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"

def _cache_df_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.csv"

def _is_fresh(path: Path, ttl_hours: float) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) < ttl_hours * 3600

def _save_json(name: str, data: Any) -> None:
    try:
        _cache_path(name).write_text(json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Cache write failed {name}: {e}")

def _load_json(name: str) -> Optional[Any]:
    p = _cache_path(name)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None

def _save_df(name: str, df: pd.DataFrame) -> None:
    try:
        df.to_csv(_cache_df_path(name), index=False)
    except Exception as e:
        logger.warning(f"DF cache write failed {name}: {e}")

def _load_df(name: str) -> Optional[pd.DataFrame]:
    p = _cache_df_path(name)
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 1. GDELT Direct CSV (No API key — completely free)
# ══════════════════════════════════════════════════════════════════════════════

GDELT_INDEX_URL = "http://data.gdeltproject.org/events/index.html"
GDELT_BASE_URL  = "http://data.gdeltproject.org/events/"

# Columns we care about from the 58-column GDELT schema
GDELT_COLS = {
    0:  "GlobalEventID",
    1:  "Day",
    5:  "Actor1Name",
    6:  "Actor1CountryCode",
    15: "Actor2Name",
    26: "EventCode",
    27: "EventBaseCode",
    28: "EventRootCode",
    29: "QuadClass",
    30: "GoldsteinScale",
    31: "NumMentions",
    34: "AvgTone",
    44: "ActionGeo_FullName",
    45: "ActionGeo_CountryCode",
    57: "SOURCEURL",
}

# Retail-relevant GDELT EventRootCode mapping
GDELT_EVENT_MAP = {
    "01": "positive_media",  # Make public statement
    "02": "positive_media",  # Appeal
    "03": "macroeconomic",   # Express intent to cooperate
    "04": "regulatory",      # Consult
    "05": "regulatory",      # Engage in diplomatic cooperation
    "06": "macroeconomic",   # Engage in material cooperation
    "07": "supply_chain",    # Provide aid
    "08": "competitor_launch",# Yield
    "09": "supply_chain",    # Investigate
    "10": "negative_media",  # Demand
    "11": "negative_media",  # Disapprove
    "12": "negative_media",  # Reject
    "13": "product_recall",  # Threaten
    "14": "geopolitical",    # Protest
    "15": "supply_chain",    # Exhibit military posture
    "16": "geopolitical",    # Reduce relations
    "17": "geopolitical",    # Coerce
    "18": "supply_chain",    # Assault
    "19": "supply_chain",    # Fight
    "20": "supply_chain",    # Use unconventional mass violence
}


def _gdelt_event_type(root_code: str) -> str:
    return GDELT_EVENT_MAP.get(str(root_code)[:2], "unknown")


def fetch_gdelt_direct(days_back: int = 3, max_rows_per_day: int = 200) -> pd.DataFrame:
    """
    Download GDELT event files directly (no API key, no BigQuery).
    Downloads the last `days_back` daily CSV.zip files, filters to India,
    returns a clean DataFrame.
    """
    cache_name = f"gdelt_india_{days_back}d"
    if _is_fresh(_cache_df_path(cache_name), ttl_hours=6):
        df = _load_df(cache_name)
        if df is not None and not df.empty:
            logger.info(f"GDELT: loaded {len(df)} rows from cache")
            return df

    # Also load the pre-downloaded file from data_sources if it exists
    local_gdelt = DATA_DIR / "geopolitical" / "raw" / "gdelt_india_20260406.csv"
    frames: List[pd.DataFrame] = []
    if local_gdelt.exists():
        try:
            raw = pd.read_csv(local_gdelt, nrows=1000)
            frames.append(_parse_gdelt_df(raw))
            logger.info(f"GDELT: loaded {len(frames[0])} rows from local file")
        except Exception as e:
            logger.warning(f"GDELT local load failed: {e}")

    # Try to download recent files
    for days_ago in range(1, days_back + 1):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
        url  = f"{GDELT_BASE_URL}{date}.export.CSV.zip"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, stream=True)
            if resp.status_code != 200:
                logger.info(f"GDELT {date}: HTTP {resp.status_code} — skipping")
                continue
            # Unzip in memory
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                fname = zf.namelist()[0]
                with zf.open(fname) as f:
                    raw = pd.read_csv(
                        f, sep="\t", header=None,
                        usecols=list(GDELT_COLS.keys()),
                        names=list(GDELT_COLS.values()),
                        on_bad_lines="skip",
                        nrows=10000,
                    )
            # Filter India
            india_mask = (
                raw["ActionGeo_CountryCode"].astype(str).str.upper() == "IN"
            )
            india_df = raw[india_mask].head(max_rows_per_day)
            if not india_df.empty:
                frames.append(_parse_gdelt_df(india_df))
                logger.info(f"GDELT {date}: {len(india_df)} India rows downloaded")
        except Exception as e:
            logger.warning(f"GDELT download failed for {date}: {e}")

    if not frames:
        logger.warning("GDELT: no data retrieved")
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["GlobalEventID"])
    _save_df(cache_name, out)
    return out


def _extract_headline_from_url(url: str) -> str:
    """
    Best-effort headline extraction from a GDELT source URL.
    Turns URL path segments into readable text (slug → title).
    """
    if not url or url in ("nan", "None", ""):
        return ""
    try:
        parts = url.split("/")
        # Find the longest meaningful slug (article title is usually the last path segment)
        candidates = [p for p in parts[3:] if len(p) > 12 and "." not in p[:5]]
        if candidates:
            slug = candidates[-1].split("?")[0].split("#")[0]
            headline = slug.replace("-", " ").replace("_", " ").replace("%20", " ")
            # Title-case, strip trailing numbers/ids
            import re
            headline = re.sub(r"\s+\d{6,}$", "", headline).strip().title()
            if len(headline) > 10:
                return headline[:120]
    except Exception:
        pass
    return ""


def _parse_gdelt_df(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise GDELT raw DataFrame into retail-friendly format."""
    df = raw.copy()

    for col in ["GlobalEventID", "Day", "Actor1Name", "Actor2Name",
                "EventRootCode", "GoldsteinScale", "AvgTone",
                "NumMentions", "ActionGeo_FullName", "SOURCEURL"]:
        if col not in df.columns:
            df[col] = None

    df["event_date"] = pd.to_datetime(df["Day"].astype(str), format="%Y%m%d", errors="coerce")
    df["event_type"] = df["EventRootCode"].astype(str).apply(lambda x: _gdelt_event_type(x[:2]))
    df["goldstein"]  = pd.to_numeric(df["GoldsteinScale"], errors="coerce").fillna(0)
    df["avg_tone"]   = pd.to_numeric(df["AvgTone"],        errors="coerce").fillna(0)
    df["mentions"]   = pd.to_numeric(df["NumMentions"],    errors="coerce").fillna(1)
    df["location"]   = df["ActionGeo_FullName"].fillna("India").astype(str)
    df["url_raw"]    = df["SOURCEURL"].fillna("").astype(str)

    # ── Demand impact: goldstein scale drives direction ───────────────────────
    # Positive goldstein (+10 = most cooperative) → demand benefit for retail
    # Negative goldstein (-10 = most conflictual) → demand disruption
    # Scale to ±20% range (electronics retail sensitivity)
    df["impact_score"]     = (df["goldstein"].abs() / 10.0).clip(0, 1)
    df["demand_change_pct"] = (df["goldstein"] * df["impact_score"] * 2.0).round(1)
    # Clamp to realistic range: -25% to +25%
    df["demand_change_pct"] = df["demand_change_pct"].clip(-25, 25)

    df["direction"] = df["goldstein"].apply(
        lambda g: "negative" if g < -0.5 else ("positive" if g > 0.5 else "neutral")
    )

    # ── Build human-readable title ────────────────────────────────────────────
    def _make_title(row) -> str:
        # 1. Try to extract headline from source URL
        headline = _extract_headline_from_url(str(row.get("url_raw", "")))
        if headline:
            return headline

        # 2. Fallback: event type label + location
        etype = str(row.get("event_type", ""))
        loc   = str(row.get("location", "India"))[:50].split(",")[0].strip()
        etype_labels = {
            "supply_chain": "Supply Chain Event",
            "macroeconomic": "Macroeconomic Development",
            "regulatory": "Regulatory Action",
            "geopolitical": "Geopolitical Event",
            "positive_media": "Positive Market Signal",
            "negative_media": "Market Concern Reported",
            "competitor_launch": "Competitor Activity",
            "product_recall": "Product/Safety Alert",
        }
        label = etype_labels.get(etype, "India Market Event")
        return f"{label} — {loc}"

    df["title"] = df.apply(_make_title, axis=1)
    df["source_domain"] = df["url_raw"].apply(
        lambda u: u.split("/")[2].replace("www.", "") if u.count("/") >= 2 else "GDELT"
    )

    # ── Quality filter: drop rows with no real URL or very low mentions ───────
    has_url = df["url_raw"].str.startswith("http")
    df = df[has_url | (df["mentions"] > 3)].copy()

    return df[[
        "GlobalEventID", "event_date", "event_type", "title",
        "source_domain", "goldstein", "avg_tone", "mentions",
        "impact_score", "demand_change_pct", "direction", "location", "url_raw",
    ]].rename(columns={
        "url_raw": "url",
        "source_domain": "source",
        "event_date": "published_at",
    })


def gdelt_to_events_dict(df: pd.DataFrame) -> List[Dict]:
    """Convert GDELT DataFrame to the standard events list format used by the app."""
    events = []
    seen_titles: set = set()
    for _, row in df.iterrows():
        title = str(row.get("title", "India Market Event"))
        # Deduplicate by normalised title prefix
        title_key = title[:40].lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        url = str(row.get("url", ""))
        # Only include real HTTP URLs; skip internal GDELT placeholders
        clean_url = url if url.startswith("http") else ""

        events.append({
            "title":              title,
            "body":               str(row.get("location", "")),
            "url":                clean_url,
            "source":             str(row.get("source", "GDELT")),
            "published_at":       str(row.get("published_at", ""))[:10],
            "event_type":         str(row.get("event_type", "unknown")),
            "source_credibility": round(min(0.95, 0.5 + float(row.get("mentions", 1)) / 40), 2),
            "goldstein_scale":    round(float(row.get("goldstein", 0)), 2),
            "avg_tone":           round(float(row.get("avg_tone", 0)), 2),
            "mentions":           int(row.get("mentions", 1)),
            "demand_change_pct":  float(row.get("demand_change_pct", 0)),
            "direction":          str(row.get("direction", "neutral")),
            "duration_days":      14,
            "confidence":         round(min(0.9, float(row.get("mentions", 1)) / 80), 2),
            "raw_impact_score":   round(float(row.get("impact_score", 0)), 3),
        })
    return events


# ══════════════════════════════════════════════════════════════════════════════
# 2. Wikipedia Pageviews API (No API key — completely free)
# ══════════════════════════════════════════════════════════════════════════════

WIKI_BRANDS = {
    "Samsung":    "Samsung_Galaxy",
    "Apple":      "IPhone",
    "Xiaomi":     "Xiaomi",
    "OnePlus":    "OnePlus",
    "LG":         "LG_Electronics",
    "Sony":       "Sony",
    "Bosch":      "Bosch_(company)",
    "Whirlpool":  "Whirlpool_Corporation",
}

def fetch_wikipedia_pageviews(
    articles: Optional[Dict[str, str]] = None,
    start: str = "20240101",
    end: str   = None,
) -> pd.DataFrame:
    """
    Fetch Wikipedia monthly pageviews for brand/product articles.
    Uses the free Wikimedia REST API — no key required.
    https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...
    """
    if end is None:
        end = datetime.now().strftime("%Y%m%d")
    if articles is None:
        articles = WIKI_BRANDS

    cache_name = f"wiki_views_{start}_{end[:6]}"
    if _is_fresh(_cache_df_path(cache_name), ttl_hours=24):
        df = _load_df(cache_name)
        if df is not None and not df.empty:
            return df

    # Also load the pre-downloaded file
    local_wiki = DATA_DIR / "climate" / "wikipedia_pageviews_smartphones.csv"
    if local_wiki.exists():
        try:
            df = pd.read_csv(local_wiki, parse_dates=["date"])
            logger.info(f"Wikipedia: loaded {len(df)} rows from local file")
            _save_df(cache_name, df)
            return df
        except Exception as e:
            logger.warning(f"Wikipedia local load failed: {e}")

    rows = []
    for brand, article in articles.items():
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/"
            f"per-article/en.wikipedia/all-access/all-agents/"
            f"{article}/monthly/{start}/{end}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    ts = str(item.get("timestamp", ""))
                    rows.append({
                        "date":  pd.to_datetime(ts[:8], format="%Y%m%d", errors="coerce"),
                        "year":  int(ts[:4]) if len(ts) >= 4 else None,
                        "month": int(ts[4:6]) if len(ts) >= 6 else None,
                        "brand": brand,
                        "article": article,
                        "wikipedia_views": int(item.get("views", 0)),
                    })
                logger.info(f"Wikipedia: fetched {len(items)} months for {brand}")
            time.sleep(0.3)  # polite rate limit
        except Exception as e:
            logger.warning(f"Wikipedia fetch failed for {brand}: {e}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    _save_df(cache_name, df)
    return df


def wiki_demand_signal(df: pd.DataFrame, brand_keywords: List[str] = None) -> pd.DataFrame:
    """
    Aggregate Wikipedia views into a monthly demand signal index (0–1).
    Higher views → higher public interest → positive demand signal.
    """
    if df.empty:
        return pd.DataFrame()
    if brand_keywords:
        df = df[df["brand"].str.lower().isin([k.lower() for k in brand_keywords])]
    if df.empty:
        return pd.DataFrame()

    monthly = df.groupby("date")["wikipedia_views"].sum().reset_index()
    monthly = monthly.sort_values("date")
    mn, mx = monthly["wikipedia_views"].min(), monthly["wikipedia_views"].max()
    if mx > mn:
        monthly["demand_signal"] = (monthly["wikipedia_views"] - mn) / (mx - mn)
    else:
        monthly["demand_signal"] = 0.5
    return monthly


# ══════════════════════════════════════════════════════════════════════════════
# 3. World Bank API — India Macro Indicators (No key — completely free)
# ══════════════════════════════════════════════════════════════════════════════

WB_INDICATORS = {
    "FP.CPI.TOTL.ZG":   "inflation_pct",      # CPI inflation %
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",    # GDP growth %
    "NE.CON.PRVT.KD.ZG": "consumer_spend_pct",# Private consumption growth %
    "IC.BUS.EASE.XQ":    "ease_of_business",  # Ease of doing business (rank)
}

def fetch_world_bank_macro(country: str = "IN", years_back: int = 8) -> pd.DataFrame:
    """
    Fetch macro indicators from the World Bank open data API.
    No API key required. https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
    """
    cache_name = f"wb_macro_{country}_{years_back}y"
    if _is_fresh(_cache_df_path(cache_name), ttl_hours=24 * 7):  # weekly refresh
        df = _load_df(cache_name)
        if df is not None and not df.empty:
            return df

    # Load local CPI data first
    local_cpi = DATA_DIR / "climate" / "india_cpi_worldbank.csv"
    frames: List[pd.DataFrame] = []
    if local_cpi.exists():
        try:
            cpi_df = pd.read_csv(local_cpi)
            cpi_df = cpi_df[["year", "inflation_pct"]].dropna()
            frames.append(cpi_df.rename(columns={"inflation_pct": "value"}).assign(indicator="inflation_pct"))
            logger.info(f"World Bank CPI: loaded {len(cpi_df)} rows from local file")
        except Exception as e:
            logger.warning(f"World Bank local load failed: {e}")

    all_rows = []
    for indicator_code, col_name in WB_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator_code}"
            f"?format=json&per_page={years_back + 2}&mrv={years_back + 2}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                raw = resp.json()
                if len(raw) >= 2 and raw[1]:
                    for item in raw[1]:
                        if item.get("value") is not None:
                            all_rows.append({
                                "year": int(item["date"]),
                                "indicator": col_name,
                                "value": float(item["value"]),
                            })
                    logger.info(f"World Bank: fetched {col_name}")
            time.sleep(0.2)
        except Exception as e:
            logger.warning(f"World Bank fetch failed for {indicator_code}: {e}")

    if all_rows or frames:
        if all_rows:
            remote_df = pd.DataFrame(all_rows)
            frames.append(remote_df)
        combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if not combined.empty:
            # Pivot to wide format
            try:
                wide = combined.pivot_table(index="year", columns="indicator", values="value", aggfunc="mean").reset_index()
                wide.columns.name = None
                _save_df(cache_name, wide)
                return wide
            except Exception:
                pass

    return pd.DataFrame()


def macro_demand_multiplier(macro_df: pd.DataFrame, year: int) -> float:
    """
    Return a demand multiplier based on macro conditions for a given year.
    Higher inflation → lower purchasing power → multiplier < 1
    Higher GDP growth → more spending → multiplier > 1
    """
    if macro_df.empty or "year" not in macro_df.columns:
        return 1.0
    row = macro_df[macro_df["year"] == year]
    if row.empty:
        return 1.0

    multiplier = 1.0
    if "inflation_pct" in row.columns:
        inflation = float(row["inflation_pct"].iloc[0] or 0)
        multiplier *= max(0.85, 1 - (inflation - 4) * 0.02)  # >4% hurts demand

    if "gdp_growth_pct" in row.columns:
        gdp_growth = float(row["gdp_growth_pct"].iloc[0] or 0)
        multiplier *= min(1.15, 1 + gdp_growth * 0.01)  # GDP growth boosts demand

    return round(multiplier, 3)


# ══════════════════════════════════════════════════════════════════════════════
# 4. python-holidays — India Festivals (Offline — no network needed)
# ══════════════════════════════════════════════════════════════════════════════

FESTIVAL_IMPACTS = {
    "Diwali":               0.35,
    "Dussehra":             0.20,
    "Id-ul-Fitr":           0.18,
    "Bakrid":               0.15,
    "Navratri":             0.15,
    "Onam":                 0.12,
    "Christmas Day":        0.20,
    "New Year's Day":       0.18,
    "Republic Day":         0.08,
    "Independence Day":     0.10,
    "Gandhi Jayanti":       0.05,
    "Good Friday":          0.08,
    "Janmashtami":          0.10,
    "Maha Shivaratri":      0.08,
    "Holi":                 0.15,
    "Eid al-Fitr":          0.18,
    "Eid al-Adha":          0.15,
    "default":              0.07,
}

def get_india_holidays(start_year: int = 2019, end_year: int = 2027) -> pd.DataFrame:
    """
    Get Indian public holidays using the python-holidays package.
    Returns a clean DataFrame sorted by date with impact factors.
    """
    # Load pre-downloaded file first
    local = DATA_DIR / "festivals" / "raw" / "india_holidays_real.csv"
    if local.exists():
        try:
            df = pd.read_csv(local, parse_dates=["date"])
            logger.info(f"Holidays: loaded {len(df)} rows from local file")
            return df
        except Exception as e:
            logger.warning(f"Holiday local load failed: {e}")

    try:
        import holidays as hol_lib
        india = hol_lib.country_holidays("IN", years=range(start_year, end_year + 1))
        rows = []
        for date_obj, name in sorted(india.items()):
            impact = FESTIVAL_IMPACTS.get(name, FESTIVAL_IMPACTS["default"])
            rows.append({
                "date": pd.Timestamp(date_obj),
                "festival": name,
                "country": "India",
                "holiday_type": "Public Holiday",
                "impact_factor": impact,
            })
        df = pd.DataFrame(rows)
        logger.info(f"Holidays: generated {len(df)} from python-holidays package")
        return df
    except ImportError:
        logger.warning("python-holidays not installed")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# 5. Main: fetch_all_live_data — called at app startup + periodic refresh
# ══════════════════════════════════════════════════════════════════════════════

_live_data_cache: Dict[str, Any] = {}
_last_fetch_time: float = 0
REFRESH_INTERVAL_HOURS = 6


def fetch_all_live_data(force: bool = False) -> Dict[str, Any]:
    """
    Fetch all live external data in one call.
    Results cached in memory for REFRESH_INTERVAL_HOURS.
    """
    global _live_data_cache, _last_fetch_time

    if not force and _live_data_cache and (time.time() - _last_fetch_time) < REFRESH_INTERVAL_HOURS * 3600:
        return _live_data_cache

    result: Dict[str, Any] = {
        "sources_status": {},
        "gdelt_events": [],
        "wikipedia_views": pd.DataFrame(),
        "macro_data": pd.DataFrame(),
        "india_holidays": pd.DataFrame(),
        "last_fetched": datetime.now().isoformat(),
    }

    # 1. GDELT
    try:
        gdelt_df = fetch_gdelt_direct(days_back=3)
        if not gdelt_df.empty:
            result["gdelt_events"] = gdelt_to_events_dict(gdelt_df)
            result["sources_status"]["GDELT Direct CSV"] = {
                "active": True,
                "rows": len(gdelt_df),
                "last_updated": str(gdelt_df["published_at"].max())[:10] if "published_at" in gdelt_df.columns else "unknown",
                "description": "Global Database of Events (free direct CSV, no key needed)",
                "latency": "Same-day data",
            }
        else:
            result["sources_status"]["GDELT Direct CSV"] = {"active": False, "reason": "No data returned"}
    except Exception as e:
        result["sources_status"]["GDELT Direct CSV"] = {"active": False, "reason": str(e)[:80]}

    # 2. Wikipedia Pageviews
    try:
        wiki_df = fetch_wikipedia_pageviews(start="20230101")
        if not wiki_df.empty:
            result["wikipedia_views"] = wiki_df
            result["sources_status"]["Wikipedia Pageviews API"] = {
                "active": True,
                "rows": len(wiki_df),
                "brands": wiki_df["brand"].nunique() if "brand" in wiki_df.columns else 0,
                "description": "Wikimedia REST API — brand interest trends (free, no key)",
                "latency": "Monthly data",
            }
        else:
            result["sources_status"]["Wikipedia Pageviews API"] = {"active": False, "reason": "Empty response"}
    except Exception as e:
        result["sources_status"]["Wikipedia Pageviews API"] = {"active": False, "reason": str(e)[:80]}

    # 3. World Bank Macro
    try:
        macro_df = fetch_world_bank_macro()
        if not macro_df.empty:
            result["macro_data"] = macro_df
            result["sources_status"]["World Bank Open Data API"] = {
                "active": True,
                "indicators": [c for c in macro_df.columns if c != "year"],
                "description": "World Bank API — India macro indicators (free, no key)",
                "latency": "Annual data",
            }
        else:
            result["sources_status"]["World Bank Open Data API"] = {"active": False, "reason": "Empty response"}
    except Exception as e:
        result["sources_status"]["World Bank Open Data API"] = {"active": False, "reason": str(e)[:80]}

    # 4. India Holidays (offline)
    try:
        holidays_df = get_india_holidays()
        if not holidays_df.empty:
            result["india_holidays"] = holidays_df
            result["sources_status"]["python-holidays (India)"] = {
                "active": True,
                "rows": len(holidays_df),
                "description": "Official Indian public holidays 2019-2027 (offline package)",
                "latency": "Offline",
            }
        else:
            result["sources_status"]["python-holidays (India)"] = {"active": False, "reason": "Package not installed"}
    except Exception as e:
        result["sources_status"]["python-holidays (India)"] = {"active": False, "reason": str(e)[:80]}

    _live_data_cache = result
    _last_fetch_time = time.time()

    active_count = sum(1 for s in result["sources_status"].values() if s.get("active"))
    logger.info(f"Live data fetch complete: {active_count}/{len(result['sources_status'])} sources active")
    return result



# ── Electronics retail relevance scoring ─────────────────────────────────────
# Keywords that make a GDELT event relevant to Indian consumer electronics retail

_RELEVANCE_URL_KEYWORDS = [
    # brands
    "samsung", "apple", "iphone", "xiaomi", "redmi", "oneplus", "oppo", "vivo",
    "realme", "nokia", "motorola", "lg", "sony", "dell", "hp", "lenovo", "asus",
    "acer", "bosch", "whirlpool", "daikin", "voltas", "godrej", "haier",
    # categories
    "smartphone", "mobile", "laptop", "tablet", "television", "tv", "smarttv",
    "headphone", "earphone", "washing-machine", "refrigerator", "air-condition",
    "electronics", "gadget", "tech", "consumer-electronics",
    # market signals
    "inflation", "gst", "tariff", "import-duty", "semiconductor", "supply-chain",
    "festive", "diwali", "sale", "discount", "ecommerce", "flipkart", "amazon",
    "retail", "consumer-spending", "purchasing-power", "rupee", "rbi", "sensex",
    # trade/macro
    "china-india", "trade-war", "chip-shortage", "5g", "electric-vehicle",
    "manufacturing", "make-in-india", "production-linked",
]

_RELEVANCE_ACTOR_KEYWORDS = [
    "SAMSUNG", "APPLE", "XIAOMI", "SONY", "LG", "DELL", "LENOVO", "ASUS",
    "AMAZON", "FLIPKART", "RELIANCE", "TATA", "INFOSYS", "WIPRO",
    "INDIA", "GOVERNMENT OF INDIA", "MINISTRY", "RBI", "SEBI",
    "CONSUMER", "TECH", "RETAIL", "TRADE", "MANUFACTURE",
]

# GDELT event types that are always macro-relevant for electronics retail
_ALWAYS_RELEVANT_TYPES = {"macroeconomic", "regulatory", "supply_chain", "competitor_launch", "product_recall"}


def _electronics_relevance_score(event: Dict) -> float:
    """
    Return a 0–1 relevance score for an electronics retail context.
    Events scoring < 0.25 are filtered out as noise.
    """
    score = 0.0
    url   = str(event.get("url", "")).lower()
    title = str(event.get("title", "")).lower()
    etype = str(event.get("event_type", ""))
    src   = str(event.get("source", "")).lower()

    # Macro-relevant event types always pass
    if etype in _ALWAYS_RELEVANT_TYPES:
        score += 0.35

    # URL / title keyword match
    combined_text = url + " " + title + " " + src
    keyword_hits = sum(1 for kw in _RELEVANCE_URL_KEYWORDS if kw in combined_text)
    score += min(0.65, keyword_hits * 0.15)

    # High-credibility sources (known tech/business outlets)
    tech_domains = [
        "techcrunch", "gadgets360", "91mobiles", "ndtv", "economictimes",
        "livemint", "moneycontrol", "business-standard", "thehindubusiness",
        "techradar", "gsmarena", "digit.in", "bgr", "theverge", "reuters",
        "bloomberg", "financialexpress",
    ]
    if any(d in src for d in tech_domains):
        score += 0.3

    return min(1.0, score)


def filter_electronics_relevant(events: List[Dict], min_score: float = 0.25) -> List[Dict]:
    """Keep only events relevant to electronics retail. Attach relevance_score."""
    scored = []
    for ev in events:
        sc = _electronics_relevance_score(ev)
        if sc >= min_score:
            ev = dict(ev)
            ev["relevance_score"] = round(sc, 2)
            scored.append(ev)
    scored.sort(key=lambda e: (e["relevance_score"], abs(float(e.get("demand_change_pct", 0)))), reverse=True)
    return scored


def get_live_events_feed(limit: int = 50) -> Dict[str, Any]:
    """
    Return a ready-to-serve events feed combining:
      - GDELT (filtered to electronics-relevant events)
      - Real India festivals from python-holidays (always relevant)
      - World Bank macro signals (always relevant)
    """
    live = fetch_all_live_data()
    raw_gdelt = list(live.get("gdelt_events", []))

    # ── Filter GDELT to electronics-relevant events ───────────────────────────
    relevant_gdelt = filter_electronics_relevant(raw_gdelt, min_score=0.25)
    events = relevant_gdelt

    # ── Upcoming India festivals (always relevant — drive demand +10–35%) ─────
    holidays_df = live.get("india_holidays", pd.DataFrame())
    if not isinstance(holidays_df, pd.DataFrame):
        holidays_df = pd.DataFrame()

    if not holidays_df.empty:
        today = datetime.now()
        upcoming = holidays_df[
            pd.to_datetime(holidays_df["date"]) >= pd.Timestamp(today - timedelta(days=30))
        ].head(12)
        for _, h in upcoming.iterrows():
            impact = float(h.get("impact_factor", 0.1))
            festival = str(h.get("festival", "Holiday"))
            events.append({
                "title": f"{festival} — Electronics demand uplift expected",
                "body": "Indian public holiday: consumer electronics sales typically surge ±7 days around this date",
                "url": "https://www.timesofindia.com/india/festivals",
                "source": "python-holidays (India)",
                "published_at": str(h["date"])[:10],
                "event_type": "positive_media",
                "source_credibility": 1.0,
                "demand_change_pct": round(impact * 100, 1),
                "direction": "positive",
                "duration_days": 14,
                "confidence": 0.95,
                "raw_impact_score": impact,
                "relevance_score": 1.0,
                "price_signal": "hold_or_raise",
                "price_signal_reason": f"{festival} drives +{impact*100:.0f}% demand — sustain or slightly increase price",
            })

    # ── World Bank macro signals (always relevant for pricing) ────────────────
    macro_df = live.get("macro_data", pd.DataFrame())
    if not isinstance(macro_df, pd.DataFrame):
        macro_df = pd.DataFrame()
    if not macro_df.empty and "inflation_pct" in macro_df.columns:
        latest = macro_df.sort_values("year").iloc[-1]
        inflation = float(latest.get("inflation_pct", 0) or 0)
        year = int(latest.get("year", 0))
        if inflation > 0:
            direction = "negative" if inflation > 5 else "neutral"
            demand_chg = round(-(max(0, inflation - 4)) * 2, 1)
            price_signal = "lower" if inflation > 6 else ("hold" if inflation > 4 else "raise")
            events.append({
                "title": f"India CPI Inflation: {inflation:.1f}% in {year} (World Bank)",
                "body": "High inflation erodes consumer purchasing power for discretionary electronics",
                "url": "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=IN",
                "source": "World Bank API",
                "published_at": f"{year}-12-31",
                "event_type": "macroeconomic",
                "source_credibility": 0.98,
                "demand_change_pct": demand_chg,
                "direction": direction,
                "duration_days": 365,
                "confidence": 0.92,
                "raw_impact_score": min(0.8, inflation / 10),
                "relevance_score": 1.0,
                "price_signal": price_signal,
                "price_signal_reason": (
                    f"CPI at {inflation:.1f}% → purchasing power under pressure. "
                    f"{'Consider price cuts to maintain volume.' if inflation > 6 else 'Monitor closely.'}"
                ),
            })

        gdp_growth = float(latest.get("gdp_growth_pct", 0) or 0) if "gdp_growth_pct" in latest.index else 0
        if gdp_growth > 0:
            events.append({
                "title": f"India GDP Growth: {gdp_growth:.1f}% in {year} (World Bank)",
                "body": "Strong economic growth boosts consumer spending on electronics",
                "url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=IN",
                "source": "World Bank API",
                "published_at": f"{year}-12-31",
                "event_type": "macroeconomic",
                "source_credibility": 0.98,
                "demand_change_pct": round(min(10, gdp_growth * 0.8), 1),
                "direction": "positive" if gdp_growth > 5 else "neutral",
                "duration_days": 365,
                "confidence": 0.88,
                "raw_impact_score": min(0.6, gdp_growth / 10),
                "relevance_score": 1.0,
                "price_signal": "raise" if gdp_growth > 6 else "hold",
                "price_signal_reason": (
                    f"GDP growing at {gdp_growth:.1f}% — consumer spending healthy. "
                    f"{'Room to sustain premium pricing.' if gdp_growth > 6 else 'Stable demand environment.'}"
                ),
            })

    # ── Sort: relevance first, then absolute demand impact ───────────────────
    events.sort(
        key=lambda e: (e.get("relevance_score", 0), abs(float(e.get("demand_change_pct", 0)))),
        reverse=True,
    )

    sources_status = live.get("sources_status", {})
    active_sources = [k for k, v in sources_status.items() if v.get("active")]

    # Build summary
    by_type: Dict[str, int] = {}
    high_impact = 0
    neg_impact = 0.0
    pos_impact = 0.0
    for ev in events:
        t = ev.get("event_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        chg = float(ev.get("demand_change_pct", 0))
        if abs(chg) > 8:
            high_impact += 1
        if chg < 0:
            neg_impact += chg
        else:
            pos_impact += chg

    return {
        "events": events[:limit],
        "summary": {
            "total_events": len(events),
            "by_type": by_type,
            "high_impact_count": high_impact,
            "net_positive_impact_pct": round(pos_impact, 1),
            "net_negative_impact_pct": round(neg_impact, 1),
        },
        "data_sources": active_sources,
        "sources_detail": sources_status,
        "last_updated": live.get("last_fetched", datetime.now().isoformat()),
        "api_keys_required": False,
    }


# ── Event → Price Signal Engine ───────────────────────────────────────────────

# How each event type shifts the optimal price for electronics retail
_EVENT_PRICE_SIGNAL_MAP = {
    "supply_chain":      {"direction": "raise",  "strength": 0.04, "reason": "Supply disruption → scarcity premium applicable"},
    "regulatory":        {"direction": "raise",  "strength": 0.03, "reason": "Regulatory/GST changes may increase costs"},
    "macroeconomic":     {"direction": "lower",  "strength": 0.03, "reason": "Macro headwinds reduce consumer purchasing power"},
    "geopolitical":      {"direction": "lower",  "strength": 0.02, "reason": "Geopolitical uncertainty dampens discretionary spending"},
    "positive_media":    {"direction": "raise",  "strength": 0.05, "reason": "Positive sentiment / festival season — demand surge"},
    "negative_media":    {"direction": "lower",  "strength": 0.03, "reason": "Negative press — protect volume with price discipline"},
    "competitor_launch": {"direction": "lower",  "strength": 0.04, "reason": "Competitor activity — defend market share"},
    "product_recall":    {"direction": "lower",  "strength": 0.06, "reason": "Product/safety concern — reduce price to clear stock"},
}


def get_event_price_signals(category: str = "Electronics") -> Dict[str, Any]:
    """
    Aggregate live events into a net price signal for a product category.

    Returns:
      {
        net_adjustment_pct: float,   # suggested price adjustment (-10 to +10%)
        direction: "raise"|"lower"|"hold",
        signals: [{event_type, title, adjustment_pct, reason, url, source}],
        summary: str,
      }
    """
    try:
        feed = get_live_events_feed(limit=100)
    except Exception:
        return {"net_adjustment_pct": 0.0, "direction": "hold", "signals": [], "summary": "No live data available"}

    events = feed.get("events", [])
    signals: List[Dict] = []
    net_pct = 0.0

    for ev in events:
        etype = ev.get("event_type", "unknown")
        sig_def = _EVENT_PRICE_SIGNAL_MAP.get(etype)
        if not sig_def:
            continue

        # Weight by: relevance_score × confidence × |demand_change_pct| normalised
        relevance   = float(ev.get("relevance_score", 0.3))
        confidence  = float(ev.get("confidence", 0.5))
        demand_chg  = abs(float(ev.get("demand_change_pct", 0)))
        demand_norm = min(1.0, demand_chg / 20.0)   # normalise to 0-1

        weight     = relevance * confidence * (0.5 + 0.5 * demand_norm)
        adjustment = sig_def["strength"] * weight * 100  # in %

        if sig_def["direction"] == "lower":
            adjustment = -adjustment

        # Override with explicit price_signal if present
        if "price_signal" in ev:
            ps = ev["price_signal"]
            if ps in ("lower", "raise", "hold"):
                adjustment = abs(adjustment) * (1 if ps == "raise" else (-1 if ps == "lower" else 0))

        net_pct += adjustment
        signals.append({
            "event_type":     etype,
            "title":          ev.get("title", ""),
            "adjustment_pct": round(adjustment, 2),
            "reason":         ev.get("price_signal_reason") or sig_def["reason"],
            "url":            ev.get("url", ""),
            "source":         ev.get("source", ""),
            "published_at":   ev.get("published_at", ""),
            "relevance_score": round(relevance, 2),
        })

    # Clamp net to ±8%
    net_pct = float(np.clip(net_pct, -8.0, 8.0))
    direction = "raise" if net_pct > 0.5 else ("lower" if net_pct < -0.5 else "hold")

    # Top 5 most influential signals
    signals.sort(key=lambda s: abs(s["adjustment_pct"]), reverse=True)
    top_signals = signals[:5]

    summary_parts = []
    if direction == "raise":
        summary_parts.append(f"Events suggest +{net_pct:.1f}% price opportunity")
    elif direction == "lower":
        summary_parts.append(f"Events suggest {net_pct:.1f}% price pressure")
    else:
        summary_parts.append("Events suggest holding current price")

    if top_signals:
        summary_parts.append(f"Key driver: {top_signals[0]['title'][:60]}")

    return {
        "net_adjustment_pct": round(net_pct, 2),
        "direction":          direction,
        "signals":            top_signals,
        "all_signals_count":  len(signals),
        "summary":            " — ".join(summary_parts),
    }
