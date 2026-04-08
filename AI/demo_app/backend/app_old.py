from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .data_loader import load_all
from .forecasting import forecast_monthly_demand
from .models import Recommendation
from .pricing import recommend_price
from .risk import market_risk
from .sentiment import sentiment_score

app = FastAPI(title="BluePill AI Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

DATA: Dict = {}


@app.on_event("startup")
async def startup_event() -> None:
    global DATA
    DATA = load_all()


@app.get("/api/recommendation")
def get_recommendation(
    sku: str = Query("TV-IND-001"),
    region: str = Query("India"),
) -> Dict:
    sales = DATA["sales"]
    festivals = DATA["festivals"]
    competitor_prices = DATA["competitor_prices"]
    reviews = DATA["reviews"]
    geopolitical = DATA["geopolitical"]

    sku_rows = sales[sales["sku"] == sku]
    if sku_rows.empty:
        return {"error": f"SKU not found: {sku}"}

    latest = sku_rows.sort_values("date").iloc[-1]
    product = latest["product"]
    brand = latest["brand"]
    current_price = float(latest["price"])

    forecast, confidence, forecast_drivers = forecast_monthly_demand(
        sales, festivals, sku
    )
    recommended_price, expected_profit, discount_pct, price_drivers = recommend_price(
        sales, competitor_prices, sku, forecast
    )
    sentiment = sentiment_score(reviews, sku)
    risk_score, risk_notes = market_risk(geopolitical, region)

    drivers = forecast_drivers + price_drivers
    risks = [f"Geopolitical risk score: {risk_score:.2f}"] + risk_notes

    market_summary = (
        "Demand forecast accounts for festivals and recent sales trends. "
        "Pricing recommendation balances elasticity, competitor anchors, and cost floor."
    )

    rec = Recommendation(
        sku=sku,
        product=product,
        brand=brand,
        current_price=current_price,
        recommended_price=recommended_price,
        recommended_discount_pct=discount_pct,
        expected_monthly_demand=forecast,
        expected_monthly_profit=expected_profit,
        confidence=confidence,
        drivers=drivers,
        risks=risks,
        sentiment_score=sentiment,
        market_summary=market_summary,
        metadata={"region": region},
    )

    return rec.to_dict()


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
