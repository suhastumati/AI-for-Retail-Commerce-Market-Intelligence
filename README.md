# BluePill AI — Retail Intelligence Platform

End-to-end AI-powered decision intelligence for retail pricing, inventory, and market analytics.

## Project Structure

```
├── design.md                          # System architecture document
├── requirements.md                    # Functional requirements specification
├── requirements.txt                   # Python dependencies
├── demand_forecast_sentiment_bedrock.ipynb  # AWS Bedrock integration notebook
│
├── AI/
│   ├── ai_processing_layer/           # Core AI modules
│   │   ├── sentiment_analysis/        # ✅ IMPLEMENTED — NLP pipeline (5 models, ABSA, fraud detection)
│   │   ├── demand_forecasting/        # 🔲 TO BUILD — Prophet, XGBoost, LSTM, TimesFM
│   │   ├── pricing_optimization/      # 🔲 TO BUILD — Elasticity, dynamic pricing engine
│   │   ├── market_events_risk/        # 🔲 TO BUILD — GDELT, NewsAPI, event impact scoring
│   │   ├── explainability/            # 🔲 TO BUILD — SHAP, LIME attributions
│   │   ├── copilot_reasoning/         # 🔲 TO BUILD — AI copilot with grounding & prompts
│   │   └── human_review/             # 🔲 TO BUILD — Audit trails, approval workflows
│   │
│   ├── data_sources/                  # Raw data lake
│   │   ├── sales_data/raw/            # sales.csv (144 rows, monthly SKU sales)
│   │   ├── customer_reviews/raw/      # reviews.csv (1,328 reviews, multilingual)
│   │   ├── competitor_prices/raw/     # competitor_prices.csv (192 entries)
│   │   ├── climate/raw/              # weather.csv (72 months, India)
│   │   ├── geopolitical/raw/         # events.csv (12 events)
│   │   └── festivals/raw/            # festivals.csv (28 Indian festivals)
│   │
│   └── demo_app/                      # FastAPI prototype application
│       ├── backend/                   # API: forecasting, pricing, sentiment, risk
│       ├── frontend/                  # Vanilla HTML/CSS/JS dashboard
│       └── scripts/                   # Data generation & scraping utilities
│
└── Research_Papers/                   # Reference papers (N-BEATS, TFT, C-SHAP)
```

## Modules Overview

| Module | Status | What It Does |
|--------|--------|-------------|
| **Sentiment Analysis** | ✅ Complete | 5-model ensemble (BERT, GoEmotions, sarcasm, star-rating), ABSA, fraud detection, web scraping |
| **Demand Forecasting** | 🔲 Planned | Time-series models (ARIMA, Prophet, XGBoost, LSTM) with festival/weather/sentiment signals |
| **Pricing Optimization** | 🔲 Planned | Price elasticity estimation, competitor anchoring, profit-maximizing optimization |
| **Market Events & Risk** | 🔲 Planned | GDELT geopolitical events, NewsAPI aggregation, event impact scoring |
| **Explainability** | 🔲 Planned | SHAP/LIME attributions for all model decisions |
| **AI Copilot** | 🔲 Planned | Conversational "why" and "what-if" interface via AWS Bedrock |
| **Human Review** | 🔲 Planned | Approval workflows, audit trails for pricing/inventory decisions |

## Quick Start

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the demo app
cd AI/demo_app
uvicorn backend.app:app --reload --port 8000
# Open http://localhost:8000
```

## Decision Flow

```
Customer Reviews → Sentiment Analysis ─┐
Sales History → Demand Forecasting ─────┤
Competitor Prices → Price Intelligence ─┤→ Pricing & Inventory Decision Engine
News/Events → Risk Scoring ─────────────┤
Weather/Festivals → External Signals ───┘
                                         ↓
                              Actionable Recommendations
                              (with explainability + human review)
```
