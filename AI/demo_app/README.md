# BluePill AI Demo (India • Electronics)

This is a working prototype that simulates demand forecasting, dynamic pricing, sentiment signals, and risk insights.

## What it does
- Takes a SKU input (TV or Smartphone)
- Forecasts next-month demand using seasonality + festivals
- Estimates price elasticity and recommends a profit-safe price
- Shows sentiment and geopolitical risk drivers

## How to run
1. Create a virtual environment
   - `python -m venv .venv`
2. Install dependencies
   - `.venv/bin/python -m pip install -r requirements.txt`
3. Generate sample data
   - `.venv/bin/python scripts/generate_synthetic_data.py`
4. Start the backend
   - `.venv/bin/python -m uvicorn backend.app:app --reload --port 8000`
5. Open the UI
   - http://localhost:8000

## Swap in AWS services later
- Replace `forecasting.py` with Amazon Forecast outputs
- Replace `sentiment.py` with Amazon Comprehend outputs
- Replace `risk.py` with Bedrock + news ingestion
- Replace `pricing.py` with a SageMaker endpoint

## Optional: simulate competitor scraping
- `.venv/bin/python scripts/scrape_competitor_prices.py`
