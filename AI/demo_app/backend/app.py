"""
FastAPI application – serves the Retail Intelligence Dashboard.
"""
from __future__ import annotations
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.data_loader import load_all
from backend.analytics import RetailAnalytics

# ── startup ───────────────────────────────────────────────────────────────
print("\n⏳ Loading datasets …")
DATA = load_all()
print("⏳ Computing analytics …")
engine = RetailAnalytics(DATA)
print("✅ Retail Intelligence Engine ready.\n")

# Thread pool for CPU-bound forecast (Prophet MCMC runs in a thread)
_forecast_pool = ThreadPoolExecutor(max_workers=2)

# ── app ───────────────────────────────────────────────────────────────────
app = FastAPI(title="BluePill AI – Retail Intelligence", version="3.0.0")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


# ── pages ─────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(str(FRONTEND / "index.html"))


# ── API routes ────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
async def api_dashboard():
    return JSONResponse({
        "kpis":     engine.dashboard_kpis(),
        "trend":    engine.revenue_trend(),
        "alerts":   engine.generate_alerts(),
        "products": engine.get_products(),
    })


@app.get("/api/products")
async def api_products():
    return JSONResponse(engine.get_products())


@app.get("/api/product/{sku}")
async def api_product(sku: str):
    products = engine.get_products()
    match = [p for p in products if p["sku"] == sku]
    if not match:
        return JSONResponse({"error": "SKU not found"}, status_code=404)
    return JSONResponse({
        "product":   match[0],
        "timeseries": engine.sales_timeseries(sku),
        "sentiment_trend": engine.sentiment_trend(sku),
    })


@app.get("/api/pricing")
async def api_pricing():
    return JSONResponse(engine.pricing_analysis())


@app.get("/api/inventory")
async def api_inventory():
    return JSONResponse(engine.inventory_analysis())


@app.get("/api/sentiment")
async def api_sentiment():
    return JSONResponse(engine.sentiment_overview())


@app.get("/api/sentiment/{sku}")
async def api_sentiment_sku(sku: str):
    overview = engine.sentiment_overview()
    per_sku = overview.get("per_sku", {})
    if sku not in per_sku:
        return JSONResponse({"error": "SKU not found"}, status_code=404)
    return JSONResponse({
        **per_sku[sku],
        "trend": engine.sentiment_trend(sku),
    })


@app.get("/api/competitors")
async def api_competitors():
    return JSONResponse(engine.competitor_analysis())


@app.get("/api/events")
async def api_events():
    return JSONResponse({
        "festivals": engine.festival_impacts(),
        "alerts": engine.generate_alerts(),
    })


# ── NEW: Demand Forecasting endpoints ────────────────────────────────────────
@app.get("/api/forecast")
async def api_forecast_all(horizon: int = Query(default=8, ge=2, le=24)):
    """Demand forecasts for all SKUs — runs Prophet in thread pool to avoid blocking."""
    loop = asyncio.get_event_loop()
    forecasts = await loop.run_in_executor(
        _forecast_pool, lambda: engine.demand_forecast(horizon_weeks=horizon)
    )
    return JSONResponse(forecasts)


@app.get("/api/forecast/{sku}")
async def api_forecast_sku(sku: str, horizon: int = Query(default=8, ge=2, le=24)):
    """Demand forecast for a single SKU — non-blocking."""
    loop = asyncio.get_event_loop()
    fc = await loop.run_in_executor(
        _forecast_pool, lambda: engine.demand_forecast(sku=sku, horizon_weeks=horizon)
    )
    return JSONResponse(fc)


# ── NEW: News & Events endpoints ──────────────────────────────────────────────
@app.get("/api/news")
async def api_news():
    """
    Live aggregated news and geopolitical events.
    Sources (all zero API keys):
      - GDELT Direct CSV (global events, India-filtered, updates every 15 min)
      - python-holidays India (upcoming festivals with demand uplift)
      - World Bank API (macro inflation / GDP signals)
    """
    result = engine.news_events_aggregated()
    return JSONResponse(result)


@app.get("/api/data-sources")
async def api_data_sources():
    """
    Status of all live data sources — which are active, rows fetched, last update.
    Returns short-key dict for frontend: gdelt, holidays, worldbank, wikipedia.
    """
    try:
        from backend.live_data_fetcher import fetch_all_live_data
        live = fetch_all_live_data()
        raw = live.get("sources_status", {})

        # Remap long names → short keys the frontend expects
        KEY_MAP = {
            "GDELT Direct CSV":          "gdelt",
            "python-holidays (India)":   "holidays",
            "World Bank Open Data API":  "worldbank",
            "Wikipedia Pageviews API":   "wikipedia",
        }
        sources: dict = {}
        for long_key, short_key in KEY_MAP.items():
            info = raw.get(long_key, {})
            sources[short_key] = {
                "status":       "active" if info.get("active") else "inactive",
                "rows":         info.get("rows", 0),
                "last_updated": info.get("last_updated", info.get("latency", "")),
                "description":  info.get("description", ""),
            }

        return JSONResponse({
            "sources": sources,
            "last_updated": live.get("last_fetched", ""),
            "api_keys_required": False,
            "note": "All sources are free and open — no API keys needed",
        })
    except Exception as e:
        return JSONResponse({"error": str(e), "sources": {}}, status_code=500)


# ── NEW: Profit Margin endpoints ──────────────────────────────────────────────
@app.get("/api/profit")
async def api_profit():
    """Full cost-stack margin analysis for all SKUs."""
    return JSONResponse(engine.profit_margins())


@app.get("/api/profit/scenario/{sku}")
async def api_profit_scenario(sku: str):
    """
    What-if price scenario analysis for a single SKU.
    Returns optimal price, scenario table, decision matrix, and rationale.
    """
    result = engine.profit_scenario(sku)
    if not result:
        return JSONResponse({"error": "SKU not found or insufficient data"}, status_code=404)
    return JSONResponse(result)


# ── NEW: Live Competitor Prices endpoint ──────────────────────────────────────
@app.get("/api/competitors/live")
async def api_competitors_live():
    """
    Live competitor price monitoring (scrapes + estimates).
    Returns current prices, price gaps, and pricing alerts.
    """
    return JSONResponse(engine.live_competitor_prices())

