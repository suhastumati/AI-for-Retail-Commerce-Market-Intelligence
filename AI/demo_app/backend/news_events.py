"""
News & Events Aggregator Module.

Pulls live events from:
  1. NewsAPI (free tier — 100 req/day, 1-month history)
  2. GNews API (alternative free tier)
  3. GDELT BigQuery (requires google-cloud-bigquery — optional)
  4. Static geopolitical CSV (always available, no API key needed)

Classifies each article by event type and estimates demand impact.
Results are cached in /cache/ directory to avoid hitting API rate limits.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_SECONDS = 6 * 3600  # 6-hour cache

NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")   # Register free at newsapi.org
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")  # Register free at gnews.io

# Retail-relevant keyword groups
KEYWORD_GROUPS = {
    "product_recall": [
        "recall", "safety defect", "product recall", "FDA warning",
        "NREG warning", "product ban", "safety issue",
    ],
    "competitor_launch": [
        "launches", "new product launch", "unveils", "announces new",
        "available now", "pre-order", "market launch",
    ],
    "supply_chain": [
        "port strike", "shipping delay", "container shortage",
        "chip shortage", "supply chain disruption", "semiconductor shortage",
        "logistics delay", "freight rate increase",
    ],
    "regulatory": [
        "import tariff", "GST change", "duty increase", "import ban",
        "BIS certification", "policy change India", "trade restriction",
        "PLI scheme", "FSSAI notification",
    ],
    "positive_media": [
        "award winner", "best product", "recommended by", "5-star review",
        "product of the year", "editor choice", "highly rated",
    ],
    "negative_media": [
        "disappointing", "bad quality", "avoid buying", "defective",
        "poor performance", "regret purchase", "worst product",
    ],
    "geopolitical": [
        "Red Sea", "Taiwan strait", "US China trade", "Russia Ukraine",
        "supply route", "geopolitical tension", "trade war",
        "sanctions electronics",
    ],
    "macroeconomic": [
        "inflation India", "RBI rate", "consumer confidence",
        "GDP India", "retail sales India", "electronics market India",
        "e-commerce growth India",
    ],
}

# Impact score by event type (demand change fraction)
IMPACT_TABLE = {
    "product_recall":    {"direction": -1, "magnitude": 0.55, "duration_days": 14},
    "competitor_launch": {"direction": -1, "magnitude": 0.18, "duration_days": 21},
    "supply_chain":      {"direction": -1, "magnitude": 0.12, "duration_days": 30},
    "regulatory":        {"direction": -1, "magnitude": 0.22, "duration_days": 60},
    "positive_media":    {"direction": +1, "magnitude": 0.20, "duration_days": 14},
    "negative_media":    {"direction": -1, "magnitude": 0.12, "duration_days": 7},
    "geopolitical":      {"direction": -1, "magnitude": 0.10, "duration_days": 30},
    "macroeconomic":     {"direction":  0, "magnitude": 0.08, "duration_days": 90},
    "unknown":           {"direction":  0, "magnitude": 0.05, "duration_days": 7},
}


# ── Cache Helpers ─────────────────────────────────────────────────────────────

def _cache_key(url: str, params: Dict) -> str:
    raw = url + json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def _read_cache(key: str) -> Optional[List[Dict]]:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL_SECONDS:
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_cache(key: str, data: List[Dict]) -> None:
    path = CACHE_DIR / f"{key}.json"
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, default=str))
    except Exception:
        pass


# ── Event Classification ──────────────────────────────────────────────────────

def classify_event(title: str, body: str = "") -> str:
    """Rule-based event type classifier — no ML dep required."""
    text = (title + " " + body).lower()
    # Check keyword groups in priority order
    for event_type, keywords in KEYWORD_GROUPS.items():
        if any(kw.lower() in text for kw in keywords):
            return event_type
    return "unknown"


def estimate_impact(event_type: str, source_credibility: float = 0.7,
                    reach_score: float = 0.5) -> Dict[str, Any]:
    """
    Estimate demand impact of an event.

    Args:
        event_type: One of IMPACT_TABLE keys.
        source_credibility: 0–1 (1 = Reuters/BBC, 0 = unknown blog)
        reach_score: 0–1 (based on estimated audience / social shares)

    Returns:
        {demand_change_pct, direction, duration_days, confidence}
    """
    meta = IMPACT_TABLE.get(event_type, IMPACT_TABLE["unknown"])
    magnitude_pct = meta["magnitude"] * source_credibility * reach_score * 100
    return {
        "demand_change_pct": round(meta["direction"] * magnitude_pct, 1),
        "direction": "positive" if meta["direction"] > 0 else ("negative" if meta["direction"] < 0 else "neutral"),
        "duration_days": meta["duration_days"],
        "confidence": round(source_credibility * reach_score, 2),
    }


# ── API Integrations ─────────────────────────────────────────────────────────

def fetch_newsapi(query: str, days_back: int = 7) -> List[Dict]:
    """Fetch from NewsAPI free tier (100 req/day)."""
    if not NEWS_API_KEY:
        return []
    key = _cache_key("newsapi", {"q": query, "days": days_back})
    cached = _read_cache(key)
    if cached is not None:
        return cached

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 20,
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        normalized = [_normalize_newsapi(a) for a in articles]
        _write_cache(key, normalized)
        return normalized
    except Exception as e:
        logger.warning(f"NewsAPI request failed: {e}")
        return []


def _normalize_newsapi(article: Dict) -> Dict:
    title = article.get("title", "") or ""
    desc  = article.get("description", "") or ""
    src   = article.get("source", {}).get("name", "Unknown")
    return {
        "title": title,
        "body": desc,
        "url": article.get("url", ""),
        "source": src,
        "published_at": article.get("publishedAt", "")[:10],
        "event_type": classify_event(title, desc),
        "source_credibility": _credibility_score(src),
    }


def fetch_gnews(query: str, days_back: int = 7) -> List[Dict]:
    """Fetch from GNews free tier (10 req/day)."""
    if not GNEWS_API_KEY:
        return []
    key = _cache_key("gnews", {"q": query, "days": days_back})
    cached = _read_cache(key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "lang": "en",
                "max": 10,
                "apikey": GNEWS_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        normalized = [_normalize_gnews(a) for a in articles]
        _write_cache(key, normalized)
        return normalized
    except Exception as e:
        logger.warning(f"GNews request failed: {e}")
        return []


def _normalize_gnews(article: Dict) -> Dict:
    title = article.get("title", "") or ""
    desc  = article.get("description", "") or ""
    src   = article.get("source", {}).get("name", "Unknown")
    return {
        "title": title,
        "body": desc,
        "url": article.get("url", ""),
        "source": src,
        "published_at": article.get("publishedAt", "")[:10],
        "event_type": classify_event(title, desc),
        "source_credibility": _credibility_score(src),
    }


def _credibility_score(source_name: str) -> float:
    """Simple heuristic credibility from source name."""
    high = {"Reuters", "Bloomberg", "AP News", "BBC", "The Hindu",
            "Economic Times", "Mint", "LiveMint", "NDTV", "CNN"}
    medium = {"TechCrunch", "Wired", "The Verge", "AnandTech",
              "91mobiles", "Gadgets360", "Business Today"}
    if source_name in high:
        return 0.9
    if source_name in medium:
        return 0.7
    return 0.5


# ── GDELT Integration (optional) ─────────────────────────────────────────────

def fetch_gdelt_bigquery(
    topics: List[str] = None,
    days_back: int = 7,
) -> List[Dict]:
    """
    Query GDELT via Google BigQuery (free 1TB/month).
    Requires: pip install google-cloud-bigquery
    Credentials: set GOOGLE_APPLICATION_CREDENTIALS env var or use ADC.
    """
    try:
        from google.cloud import bigquery
    except ImportError:
        logger.info("google-cloud-bigquery not installed — GDELT disabled")
        return []

    if topics is None:
        topics = ["electronics", "supply chain", "India retail"]

    topic_filter = " OR ".join([f"URLS LIKE '%{t}%'" for t in topics])
    start_dt = datetime.now() - timedelta(days=days_back)

    query = f"""
    SELECT
        DATEADD AS event_date,
        Actor1Name,
        Actor2Name,
        EventCode,
        GoldsteinScale,
        AvgTone,
        SOURCEURL,
        NumMentions
    FROM `gdelt-bq.gdeltv2.events`
    WHERE
        _PARTITIONTIME >= TIMESTAMP('{start_dt.strftime("%Y-%m-%d")}')
        AND (ActionGeo_CountryCode = 'IN' OR Actor1CountryCode = 'IN')
        AND NumMentions > 5
    ORDER BY NumMentions DESC
    LIMIT 50
    """

    try:
        client = bigquery.Client()
        results = client.query(query).result()
        rows = []
        for row in results:
            tone = float(row.AvgTone or 0)
            event_type = "positive_media" if tone > 2 else ("negative_media" if tone < -2 else "geopolitical")
            rows.append({
                "title": f"{row.Actor1Name or 'Unknown'} → {row.Actor2Name or 'Unknown'} (GDELT {row.EventCode})",
                "body": str(row.SOURCEURL or ""),
                "url": str(row.SOURCEURL or ""),
                "source": "GDELT",
                "published_at": str(row.event_date or "")[:10],
                "event_type": event_type,
                "source_credibility": 0.7,
                "goldstein_scale": float(row.GoldsteinScale or 0),
                "avg_tone": tone,
                "mentions": int(row.NumMentions or 0),
            })
        return rows
    except Exception as e:
        logger.warning(f"GDELT BigQuery query failed: {e}")
        return []


# ── Static CSV Fallback ───────────────────────────────────────────────────────

def enrich_static_events(events_df: pd.DataFrame) -> List[Dict]:
    """Enrich existing events.csv with impact estimates."""
    if events_df.empty:
        return []
    enriched = []
    for _, row in events_df.iterrows():
        ev_type = str(row.get("event_type", "unknown")).lower()
        # Map project's event types to our impact table keys
        type_map = {
            "supplychain": "supply_chain",
            "geopolitical": "geopolitical",
            "regulatory": "regulatory",
            "economic": "macroeconomic",
            "markettrend": "positive_media",
            "climate": "supply_chain",
            "competitive": "competitor_launch",
        }
        mapped_type = type_map.get(ev_type, "unknown")
        impact = estimate_impact(
            mapped_type,
            source_credibility=0.75,
            reach_score=float(row.get("impact_score", 0.3)),
        )
        enriched.append({
            "title": str(row.get("summary", "")),
            "body": "",
            "url": "",
            "source": "Internal Dataset",
            "published_at": str(row.get("date", ""))[:10],
            "event_type": mapped_type,
            "source_credibility": 0.75,
            "region": str(row.get("region", "Global")),
            "raw_impact_score": float(row.get("impact_score", 0)),
            "demand_change_pct": impact["demand_change_pct"],
            "direction": impact["direction"],
            "duration_days": impact["duration_days"],
            "confidence": impact["confidence"],
        })
    return sorted(enriched, key=lambda x: x["raw_impact_score"], reverse=True)


# ── Main Aggregator API ───────────────────────────────────────────────────────

def aggregate_events(
    events_df: pd.DataFrame = pd.DataFrame(),
    products: List[str] = None,
    days_back: int = 30,
    use_live_api: bool = True,
) -> Dict[str, Any]:
    """
    Aggregate events from all available sources.

    Returns:
        {
          events: [list of enriched events sorted by impact],
          summary: {total, by_type, high_impact_count, net_demand_impact_pct},
          data_sources: [list of sources actually used],
        }
    """
    if products is None:
        products = ["electronics India", "smartphone", "laptop", "appliances India"]

    all_events: List[Dict] = []
    sources_used: List[str] = []

    # 1. Static CSV events (always available)
    if not events_df.empty:
        static = enrich_static_events(events_df)
        all_events.extend(static)
        sources_used.append("Internal Dataset")

    if use_live_api:
        # 2. NewsAPI (requires key)
        for product in products[:2]:  # limit to 2 products to save quota
            for kw_group, keywords in list(KEYWORD_GROUPS.items())[:3]:
                query = f"({keywords[0]} OR {keywords[1]}) AND ({product})"
                articles = fetch_newsapi(query, days_back=min(days_back, 30))
                for a in articles:
                    impact = estimate_impact(
                        a["event_type"],
                        source_credibility=a["source_credibility"],
                        reach_score=0.6,
                    )
                    a.update(impact)
                    all_events.append(a)
                if articles:
                    if "NewsAPI" not in sources_used:
                        sources_used.append("NewsAPI")

        # 3. GNews (requires key)
        for product in products[:1]:
            for kw in list(KEYWORD_GROUPS.keys())[:2]:
                articles = fetch_gnews(f"{product} {kw}", days_back=min(days_back, 7))
                for a in articles:
                    impact = estimate_impact(
                        a["event_type"],
                        source_credibility=a["source_credibility"],
                        reach_score=0.5,
                    )
                    a.update(impact)
                    all_events.append(a)
                if articles:
                    if "GNews" not in sources_used:
                        sources_used.append("GNews")

        # 4. GDELT BigQuery (optional)
        gdelt_events = fetch_gdelt_bigquery(days_back=min(days_back, 7))
        for a in gdelt_events:
            impact = estimate_impact(a["event_type"], source_credibility=0.7, reach_score=0.5)
            a.update(impact)
            all_events.append(a)
        if gdelt_events:
            sources_used.append("GDELT BigQuery")

    # Deduplicate by title similarity (simple prefix match)
    seen_titles: set = set()
    unique_events: List[Dict] = []
    for ev in all_events:
        key = ev["title"][:60].lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            unique_events.append(ev)

    # Sort by absolute impact
    unique_events.sort(key=lambda e: abs(float(e.get("demand_change_pct", 0))), reverse=True)

    # Summary stats
    by_type: Dict[str, int] = {}
    total_neg_impact = 0.0
    total_pos_impact = 0.0
    high_impact_count = 0
    for ev in unique_events:
        ev_type = ev.get("event_type", "unknown")
        by_type[ev_type] = by_type.get(ev_type, 0) + 1
        chg = float(ev.get("demand_change_pct", 0))
        if chg < 0:
            total_neg_impact += chg
        else:
            total_pos_impact += chg
        if abs(chg) > 8:
            high_impact_count += 1

    return {
        "events": unique_events[:50],  # top 50 most impactful
        "summary": {
            "total_events": len(unique_events),
            "by_type": by_type,
            "high_impact_count": high_impact_count,
            "net_positive_impact_pct": round(total_pos_impact, 1),
            "net_negative_impact_pct": round(total_neg_impact, 1),
        },
        "data_sources": sources_used,
        "last_updated": datetime.now().isoformat(),
    }
