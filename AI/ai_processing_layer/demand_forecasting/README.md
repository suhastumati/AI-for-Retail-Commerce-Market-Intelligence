# Demand Forecasting Module

Predicts future demand at SKU level to inform inventory and pricing decisions.

## Approach (To Implement)

### Models (Ensemble)
1. **ARIMA/ETS** — Statistical baseline for stable short-term patterns
2. **Prophet** — Handles seasonality, holidays, trend changepoints
3. **XGBoost/LightGBM** — Non-linear relationships with external features
4. **LSTM** — Deep learning for complex temporal dependencies
5. **TimesFM** (Google) — Zero-shot foundation model for time-series

### Feature Sources
| Feature | Source | Update Frequency |
|---------|--------|-----------------|
| Historical sales | `data_sources/sales_data/raw/sales.csv` | Daily |
| Festival calendar | `data_sources/festivals/raw/festivals.csv` | Static |
| Weather data | `data_sources/climate/raw/weather.csv` | Daily |
| Sentiment scores | `sentiment_analysis/outputs/` | Daily |
| Competitor prices | `data_sources/competitor_prices/raw/` | 2-4x daily |
| Geopolitical events | `data_sources/geopolitical/raw/events.csv` | Real-time |

### Key Metrics
- MAPE (Mean Absolute Percentage Error): Target < 10%
- Stock-out frequency: Target < 2% of days
- Forecast horizon: 7-day, 14-day, 30-day windows

### Datasets Needed
- Minimum 2 years daily sales data (current: 12 months monthly)
- Holiday/festival data with demand uplift factors
- Weather data with temperature and rainfall

### Output
```json
{
  "sku": "TV-IND-001",
  "forecast_7d": [102, 105, 108, 112, 118, 125, 130],
  "confidence_interval": [0.85, 0.92],
  "drivers": ["Festival uplift: Diwali +30%", "Positive sentiment trend +2%/week"],
  "inventory_action": "BUY 500 units (current stock covers 3.5 days, need 10 days)"
}
```
