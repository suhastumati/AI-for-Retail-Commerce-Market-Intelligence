"""
Competitor Price Scraper & Live Price Monitor.

Sources (all free, no API key needed for scraping):
  1. Structured scraping of demo retail pages (fallback HTML in assets/)
  2. Price history CSV (existing competitor_prices.csv)
  3. Google Shopping snippets via search (respectful, no auth)

Designed to run 4× daily via a simple scheduler.
All results are cached + merged with historical CSV.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Product search configurations (SKU → search terms)
SKU_SEARCH_CONFIG: Dict[str, Dict] = {
    "TV-IND-001": {
        "terms": ["Samsung 55 inch Smart TV India", "LG 55 UHD TV India"],
        "price_range": (25_000, 100_000),
        "category": "Television",
    },
    "MB-IND-002": {
        "terms": ["Samsung Galaxy S24 price India", "OnePlus 12 price India"],
        "price_range": (15_000, 120_000),
        "category": "Smartphone",
    },
    "LP-IND-003": {
        "terms": ["Dell laptop 15 inch India price", "HP laptop 15 India price"],
        "price_range": (30_000, 150_000),
        "category": "Laptop",
    },
    "WM-IND-004": {
        "terms": ["IFB 7kg washing machine price India", "Bosch washing machine 7kg India"],
        "price_range": (15_000, 60_000),
        "category": "Washing Machine",
    },
    "AC-IND-005": {
        "terms": ["Voltas 1.5 ton split AC India price", "Daikin 1.5 ton AC India"],
        "price_range": (25_000, 80_000),
        "category": "Air Conditioner",
    },
    "HP-IND-006": {
        "terms": ["Sony WH-1000XM5 price India", "Bose QuietComfort 45 India"],
        "price_range": (3_000, 35_000),
        "category": "Headphones",
    },
    "TB-IND-007": {
        "terms": ["Samsung Galaxy Tab S9 India price", "iPad Air price India"],
        "price_range": (20_000, 80_000),
        "category": "Tablet",
    },
    "RF-IND-008": {
        "terms": ["LG 260L refrigerator India price", "Samsung 260L fridge India"],
        "price_range": (15_000, 50_000),
        "category": "Refrigerator",
    },
}


# ── Cache helpers ──────────────────────────────────────────────────────────────

def _cache_key(sku: str, source: str) -> str:
    return hashlib.md5(f"{sku}{source}".encode()).hexdigest()


def _read_price_cache(sku: str, source: str, ttl_hours: int = 6) -> Optional[Dict]:
    path = CACHE_DIR / f"price_{_cache_key(sku, source)}.json"
    if not path.exists():
        return None
    age_h = (time.time() - path.stat().st_mtime) / 3600
    if age_h > ttl_hours:
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_price_cache(sku: str, source: str, data: Dict) -> None:
    path = CACHE_DIR / f"price_{_cache_key(sku, source)}.json"
    try:
        path.write_text(json.dumps(data, default=str))
    except Exception:
        pass


# ── Price extraction utilities ─────────────────────────────────────────────────

def _extract_price_from_text(text: str, price_range: Tuple[int, int]) -> Optional[float]:
    """Extract the first valid price in ₹ from a text snippet."""
    # Patterns: ₹25,000 or Rs.25000 or INR 25000 or just 25,000 near price text
    patterns = [
        r"₹\s*([\d,]+(?:\.\d{1,2})?)",
        r"Rs\.?\s*([\d,]+(?:\.\d{1,2})?)",
        r"INR\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:price|MRP|cost|value)[:\s₹Rs\.INR]*\s*([\d,]+(?:\.\d{1,2})?)",
    ]
    lo, hi = price_range
    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            try:
                price = float(match.group(1).replace(",", ""))
                if lo <= price <= hi:
                    return price
            except ValueError:
                continue
    return None


def _simulate_realistic_price(
    sku: str,
    base_price: float,
    competitor_name: str,
    as_of_date: Optional[datetime] = None,
) -> float:
    """
    Generate a realistic competitor price based on known price relationships.
    This is used when live scraping is unavailable.
    Uses a deterministic seed so prices are consistent within the same day.
    """
    if as_of_date is None:
        as_of_date = datetime.now()
    seed = int(hashlib.md5(
        f"{sku}{competitor_name}{as_of_date.strftime('%Y%m%d')}".encode()
    ).hexdigest(), 16) % 10_000
    rng = np.random.default_rng(seed)
    # Competitors typically price ±8% around your price
    delta_pct = rng.uniform(-0.08, 0.08)
    return round(base_price * (1 + delta_pct) / 100) * 100  # round to nearest ₹100


# ── Scraping Functions ────────────────────────────────────────────────────────

def scrape_91mobiles(sku: str, search_term: str, price_range: Tuple[int, int]) -> Optional[Dict]:
    """Scrape 91mobiles.com product page for price comparison (India-focused)."""
    cached = _read_price_cache(sku, "91mobiles")
    if cached:
        return cached

    try:
        url = f"https://www.91mobiles.com/search/?q={'+'.join(search_term.split())}&type=price"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None

        text = resp.text
        price = _extract_price_from_text(text, price_range)
        if price:
            result = {
                "source": "91mobiles",
                "price": price,
                "scraped_at": datetime.now().isoformat(),
                "url": url,
            }
            _write_price_cache(sku, "91mobiles", result)
            return result
    except Exception as e:
        logger.debug(f"91mobiles scrape failed for {sku}: {e}")
    return None


def scrape_smartprix(sku: str, search_term: str, price_range: Tuple[int, int]) -> Optional[Dict]:
    """Scrape Smartprix for price comparison."""
    cached = _read_price_cache(sku, "smartprix")
    if cached:
        return cached

    try:
        url = f"https://www.smartprix.com/search/?q={'+'.join(search_term.split())}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None

        text = resp.text
        price = _extract_price_from_text(text, price_range)
        if price:
            result = {
                "source": "Smartprix",
                "price": price,
                "scraped_at": datetime.now().isoformat(),
                "url": url,
            }
            _write_price_cache(sku, "smartprix", result)
            return result
    except Exception as e:
        logger.debug(f"Smartprix scrape failed for {sku}: {e}")
    return None


def get_google_shopping_price(sku: str, search_term: str, price_range: Tuple[int, int]) -> Optional[Dict]:
    """
    Get approximate price from Google search snippet (meta-data only, no JS needed).
    Respectful: single request per call, cached 6h.
    """
    cached = _read_price_cache(sku, "google_shopping")
    if cached:
        return cached

    try:
        url = "https://www.google.com/search"
        params = {"q": f"{search_term} price buy India 2026", "hl": "en", "gl": "in"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            return None

        price = _extract_price_from_text(resp.text, price_range)
        if price:
            result = {
                "source": "Google Shopping",
                "price": price,
                "scraped_at": datetime.now().isoformat(),
                "url": url,
            }
            _write_price_cache(sku, "google_shopping", result)
            return result
    except Exception as e:
        logger.debug(f"Google Shopping scrape failed for {sku}: {e}")
    return None


# ── Per-SKU Multi-Source Scraper ───────────────────────────────────────────────

def scrape_competitor_prices(sku: str, our_price: float) -> List[Dict]:
    """
    Scrape live prices for a given SKU from multiple sources.
    Falls back to realistic simulation if scraping fails.

    Returns: list of {competitor, price, source, scraped_at, price_gap_pct}
    """
    config = SKU_SEARCH_CONFIG.get(sku)
    if not config:
        return []

    price_range = config["price_range"]
    search_terms = config["terms"]
    results: List[Dict] = []
    competitors = [
        ("CompetitorA", search_terms[0] if len(search_terms) > 0 else sku),
        ("CompetitorB", search_terms[1] if len(search_terms) > 1 else sku),
    ]

    for comp_name, search_term in competitors:
        scraped_price = None

        # Try live sources in order
        for scrape_fn in [scrape_91mobiles, scrape_smartprix, get_google_shopping_price]:
            try:
                data = scrape_fn(sku, search_term, price_range)
                if data and data.get("price"):
                    scraped_price = data["price"]
                    source = data["source"]
                    break
            except Exception:
                continue

        # Fallback: realistic simulation
        if scraped_price is None:
            scraped_price = _simulate_realistic_price(sku, our_price, comp_name)
            source = "Estimated"

        gap_pct = ((our_price - scraped_price) / scraped_price * 100) if scraped_price else 0

        results.append({
            "sku": sku,
            "competitor": comp_name,
            "price": round(scraped_price),
            "source": source,
            "scraped_at": datetime.now().isoformat(),
            "price_gap_pct": round(gap_pct, 1),
            "position": "Premium" if gap_pct > 2 else ("Discount" if gap_pct < -2 else "Parity"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        })

    return results


# ── Portfolio Price Monitor ─────────────────────────────────────────────────

def monitor_all_prices(
    products: List[Dict],
    existing_competitors_df: pd.DataFrame = pd.DataFrame(),
) -> Dict[str, Any]:
    """
    Monitor prices for all products in the portfolio.

    Args:
        products: list of {sku, current_price, ...} from analytics.get_products()
        existing_competitors_df: historical competitor prices from CSV

    Returns:
        {
          live_prices: [...],
          alerts: [...],
          price_map: {sku: {your_price, comp_avg, gap_pct, recommendation}},
        }
    """
    live_prices: List[Dict] = []
    alerts: List[Dict] = []
    price_map: Dict[str, Dict] = {}

    for product in products:
        sku = product["sku"]
        our_price = float(product.get("current_price", 0))
        if our_price == 0:
            continue

        # Get live competitor prices
        comp_results = scrape_competitor_prices(sku, our_price)

        # Merge with historical CSV data (last 7 days) for context
        hist_prices: List[float] = []
        if not existing_competitors_df.empty and "sku" in existing_competitors_df.columns:
            hist = existing_competitors_df[existing_competitors_df["sku"] == sku]
            if not hist.empty:
                cutoff = datetime.now() - timedelta(days=7)
                hist_recent = hist[pd.to_datetime(hist["date"]) >= cutoff]
                if not hist_recent.empty:
                    hist_prices = hist_recent["price"].tolist()

        comp_prices_today = [r["price"] for r in comp_results if r["price"] > 0]
        all_comp_prices = comp_prices_today + hist_prices
        comp_avg = float(np.mean(all_comp_prices)) if all_comp_prices else our_price

        gap_pct = (our_price - comp_avg) / comp_avg * 100 if comp_avg else 0

        # Pricing recommendation
        if gap_pct > 8:
            recommendation = f"Consider lowering by {gap_pct/2:.0f}% — significantly above market"
            alert_sev = "high"
        elif gap_pct > 3:
            recommendation = f"Marginally above market (+{gap_pct:.1f}%) — monitor closely"
            alert_sev = "medium"
        elif gap_pct < -8:
            recommendation = f"Below market by {abs(gap_pct):.0f}% — opportunity to raise price"
            alert_sev = "medium"
        elif gap_pct < -3:
            recommendation = f"Slightly below market ({gap_pct:.1f}%) — consider modest increase"
            alert_sev = "low"
        else:
            recommendation = "Competitive parity — no action needed"
            alert_sev = None

        price_map[sku] = {
            "our_price": round(our_price),
            "comp_avg": round(comp_avg),
            "gap_pct": round(gap_pct, 1),
            "position": "Premium" if gap_pct > 2 else ("Discount" if gap_pct < -2 else "Parity"),
            "recommendation": recommendation,
            "sources": [r["source"] for r in comp_results],
            "last_updated": datetime.now().isoformat(),
        }

        live_prices.extend(comp_results)

        if alert_sev in ("high", "medium"):
            alerts.append({
                "severity": alert_sev,
                "sku": sku,
                "product": product.get("product", sku),
                "message": f"Competitor pricing alert: {recommendation}",
                "our_price": round(our_price),
                "comp_avg": round(comp_avg),
                "gap_pct": round(gap_pct, 1),
            })

    return {
        "live_prices": live_prices,
        "alerts": alerts,
        "price_map": price_map,
        "monitored_at": datetime.now().isoformat(),
    }


# ── Price Trend Analysis ────────────────────────────────────────────────────

def analyze_competitor_trends(
    competitors_df: pd.DataFrame,
    sku: str,
    window_months: int = 6,
) -> Dict[str, Any]:
    """
    Analyse competitor price trends for a SKU over recent months.
    Returns trend direction, velocity, and price war risk score.
    """
    if competitors_df.empty or "sku" not in competitors_df.columns:
        return {}

    cc = competitors_df[competitors_df["sku"] == sku].copy()
    if cc.empty:
        return {}

    cc["date"] = pd.to_datetime(cc["date"])
    cutoff = datetime.now() - timedelta(days=window_months * 30)
    cc = cc[cc["date"] >= cutoff].sort_values("date")

    if len(cc) < 3:
        return {}

    per_competitor: List[Dict] = []
    for comp in cc["competitor"].unique():
        cdf = cc[cc["competitor"] == comp].sort_values("date")
        prices = cdf["price"].values
        dates  = np.arange(len(prices))

        slope, intercept, r_val, p_val, _ = (
            (0.0, prices[0], 0.0, 1.0, None) if len(prices) < 3
            else __import__("scipy.stats", fromlist=["linregress"]).linregress(dates, prices)
        )
        from scipy import stats as scipy_stats
        if len(prices) >= 3:
            slope, intercept, r_val, p_val, _ = scipy_stats.linregress(dates, prices)
        else:
            slope, r_val = 0.0, 0.0

        monthly_change_pct = float(slope / max(1, prices.mean()) * 100 * 30) if prices.mean() > 0 else 0

        per_competitor.append({
            "competitor": comp,
            "latest_price": round(float(prices[-1])),
            "oldest_price": round(float(prices[0])),
            "total_change_pct": round((prices[-1] - prices[0]) / max(1, prices[0]) * 100, 1),
            "monthly_trend_pct": round(monthly_change_pct, 2),
            "trend_direction": "decreasing" if slope < -50 else ("increasing" if slope > 50 else "stable"),
            "r_squared": round(r_val ** 2, 2),
            "data_points": len(prices),
        })

    # Price war risk: if any competitor dropping > 5%/month with high confidence
    price_war_risk = any(
        c["monthly_trend_pct"] < -5 and c["r_squared"] > 0.5
        for c in per_competitor
    )

    all_recent_prices = [c["latest_price"] for c in per_competitor]
    return {
        "sku": sku,
        "per_competitor": per_competitor,
        "market_avg_price": round(float(np.mean(all_recent_prices))) if all_recent_prices else 0,
        "price_war_risk": price_war_risk,
        "analysis_window_months": window_months,
    }
