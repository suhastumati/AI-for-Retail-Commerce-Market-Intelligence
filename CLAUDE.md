# BluePill AI — Retail Intelligence Platform
## Claude Code Project Context

This is an **Indian electronics retailer AI dashboard** built for the AWS AI for Bharat Hackathon.
Do NOT ask the user to re-explain the project. Read this file first every session.

---

## How to Run

```bash
cd "AI/demo_app"
../../.venv/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 1
```

**Always use `.venv/bin/python`** — NOT system `python3` or `python`.  
The venv is at: `../../.venv/` relative to `AI/demo_app/`.  
System Python 3.14 does NOT have Prophet, XGBoost, or other required packages.

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Vanilla JS + Chart.js 4 (SPA, no framework) |
| Data | Real downloaded CSVs + live free APIs |
| ML | XGBoost + NaiveETS ensemble (Prophet disabled — too slow) |

**Entry point:** `AI/demo_app/backend/app.py`  
**Frontend:** `AI/demo_app/frontend/index.html` + `app.js` + `styles.css`

---

## Product Catalog (8 SKUs)

| SKU | Product | Brand | Category |
|-----|---------|-------|---------|
| TV-IND-001 | Smart TV 55" | Samsung | Electronics |
| MB-IND-002 | Smartphone Pro | Apple | Mobile |
| LP-IND-003 | Laptop Ultra | Dell | Computing |
| WM-IND-004 | Washing Machine 7kg | LG | Appliances |
| AC-IND-005 | Air Conditioner 1.5T | Daikin | Appliances |
| HP-IND-006 | Headphones Pro | Sony | Audio |
| TB-IND-007 | Tablet 10" | Xiaomi | Computing |
| RF-IND-008 | Refrigerator 300L | Whirlpool | Appliances |

---

## Key Files

```
AI/demo_app/
  backend/
    app.py                  # FastAPI routes — all API endpoints
    analytics.py            # RetailAnalytics class — all business logic
    data_loader.py          # Loads all CSVs at startup
    demand_forecasting.py   # XGBoost + NaiveETS ensemble (Prophet disabled)
    live_data_fetcher.py    # Zero-key live APIs: GDELT, Wikipedia, World Bank, holidays
    profit_engine.py        # Cost breakdown, what-if scenario, decision matrix
    competitor_scraper.py   # Competitor price monitoring
    news_events.py          # News/events aggregation (legacy, now superseded by live_data_fetcher)
  frontend/
    index.html              # SPA shell with all view sections
    app.js                  # All rendering logic, Chart.js, API calls
    styles.css              # All styles

AI/data_sources/
  sales_data/raw/sales.csv            # 576 rows, 8 SKUs, 2019–2024
  competitor_prices/raw/competitor_prices.csv  # 1920 rows, 5 competitors
  customer_reviews/raw/reviews.csv    # 1328 rows, sentiment data
  festivals/raw/india_holidays_real.csv        # 127 rows, python-holidays 2019–2026
  geopolitical/raw/gdelt_india_20260406.csv    # 5000 rows, GDELT India snapshot
  climate/wikipedia_pageviews_smartphones.csv  # 576 rows, 8 brands
  climate/india_cpi_worldbank.csv              # 15 rows, CPI 2010–2024
  climate/india_gdp_per_capita_worldbank.csv   # 15 rows, GDP 2010–2024
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/products` | 8 SKUs with metadata |
| `GET /api/inventory` | Stock estimates + reorder points |
| `GET /api/pricing` | Optimal prices (elasticity + events + competitor) |
| `GET /api/sentiment` | Review sentiment analysis |
| `GET /api/forecast/{sku}?horizon=8` | Demand forecast (async, 3–5s) |
| `GET /api/news` | Electronics-relevant events (GDELT filtered) |
| `GET /api/data-sources` | Live source status (gdelt/holidays/worldbank/wikipedia) |
| `GET /api/profit` | Portfolio margin overview |
| `GET /api/profit/scenario/{sku}` | What-if pricing scenario |
| `GET /api/competitors/live` | Live competitor prices |

---

## Live Data Sources (Zero API Keys)

1. **GDELT Direct CSV** — `http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip`
   - Filtered to India + electronics-relevant keywords
   - 6-hour disk cache in `AI/demo_app/cache/live/`
2. **python-holidays** — offline, India 2019–2027
3. **World Bank API** — `https://api.worldbank.org/v2/country/IN/indicator/...`
4. **Wikipedia Pageviews API** — `https://wikimedia.org/api/rest_v1/metrics/pageviews/...`

---

## Pricing Logic (Event-Driven)

Price optimization uses **3 layers**:
1. **Elasticity** — detrended log-log regression (always negative, clamped −3.5 to −0.3)
2. **Competitor ceiling** — `max(comp_avg × 1.10, min_viable × 1.05, base × 1.20)`
3. **Live event signals** — `get_event_price_signals()` in `live_data_fetcher.py`
   - Maps event types → price adjustment (supply disruption → raise, inflation → lower, festival → raise)
   - Capped at ±5% nudge on top of base optimal price

---

## Demand Forecasting

- **Models**: XGBoost + NaiveETS (2-model ensemble, auto-weighted by hold-out MAE)
- **Prophet disabled** — `USE_PROPHET_IN_ENSEMBLE = False` in `demand_forecasting.py`
  - Prophet takes 30–90s per SKU (Stan MCMC), blocks the API server
  - Re-enable only if running as a batch/offline job
- **External signals**: CPI inflation multiplier, Wikipedia interest trend multiplier
- **Response time**: 3–5 seconds per SKU

---

## Frontend Views

| Nav | View ID | Renders |
|-----|---------|---------|
| Dashboard | `view-dashboard` | KPI overview, revenue trend, sentiment |
| Inventory | `view-inventory` | Stock levels, reorder alerts |
| Pricing | `view-pricing` | Optimal prices with event signals banner |
| Sentiment | `view-sentiment` | Review analysis, aspect breakdown |
| Competitors | `view-competitors` | Price comparison, war risk |
| Demand Forecast | `view-forecast` | 8-month forecast chart, model weights |
| News & Events | `view-news` | Relevance-filtered events, price signal badges |
| Profit Engine | `view-profit` | Margin breakdown, what-if scenario |

---

## Known Constraints / Decisions

- **Python version**: `.venv` uses Python 3.11/3.12. Do NOT use system Python 3.14.
- **No `fillna(method=)`**: Deprecated in pandas 2.x — use `.ffill()` / `.bfill()` instead.
- **Prophet is intentionally disabled**: Do not re-enable for synchronous API use.
- **GDELT relevance filter**: `filter_electronics_relevant(min_score=0.25)` in `live_data_fetcher.py`. Irrelevant events (tiger cubs, plane crashes) are filtered out.
- **Competitor ceiling**: Prevents recommending prices >10% above competitor average unless min-viable margin requires it.
- **6-hour cache**: All live API responses cached to `AI/demo_app/cache/live/`. Delete `.csv` files there to force refresh.
- **Sentiment scale**: `sentiment_unified` is 0–1 (not −1 to +1). Neutral = 0.5.

---

## What NOT to Do

- Do NOT regenerate or overwrite `sales.csv`, `competitor_prices.csv` — they are carefully constructed with realistic Indian market data.
- Do NOT use `fillna(method='ffill')` — use `.ffill()`.
- Do NOT start the server with `python3` or `python` — always use `../../.venv/bin/python`.
- Do NOT re-enable Prophet unless the user explicitly requests offline/batch forecasting.
- Do NOT add API key requirements — all live sources must remain zero-key.
- Do NOT use `--reload` flag with uvicorn when Prophet is enabled — it causes shutdown hangs.
