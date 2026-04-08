# Pricing Optimization Module

Calculates optimal price that maximizes profit by combining elasticity, competitor data, sentiment, and inventory constraints.

## Approach (To Implement)

### Core Components

1. **Price Elasticity Estimator**
   - Log-log regression on historical price-demand data
   - Cross-elasticity for product substitution effects
   - Causal inference (DoWhy library) for debiased estimates

2. **Competitor Price Intelligence**
   - Daily competitor price scraping (Amazon, Flipkart)
   - Price position analysis (premium/parity/discount)
   - Automated alerts on significant competitor moves

3. **Profit Maximization Engine**
   - Grid search over price range with constraints
   - Demand function: `D(p) = base_demand × (p/p_base)^elasticity`
   - Profit: `(price - total_cost) × demand(price)`

4. **Sentiment-Based Price Modulation**
   - Positive sentiment (>0.6): sustain premium pricing
   - Neutral (0.3-0.6): competitive pricing
   - Negative (<0.3): discount + fix root causes

### Decision Matrix

| Sentiment | Inventory | Competitor | Action |
|-----------|-----------|------------|--------|
| Very Positive | Low stock | Higher | **RAISE 8-15%** |
| Positive | Low stock | Parity | **RAISE 5-10%** |
| Neutral | High stock | Parity | **LOWER 5-8%** |
| Negative | High stock | Parity | **LOWER 10-15% + investigate** |

### Constraints
- Margin floor: Never below cost + 10%
- Max daily price change: ±10%
- Competitor cap: Never exceed nearest competitor by >5%

### Output
```json
{
  "sku": "TV-IND-001",
  "current_price": 25000,
  "recommended_price": 26000,
  "elasticity": -0.8,
  "expected_demand": 96,
  "expected_profit": 846400,
  "margin_pct": 31.5,
  "confidence": 0.82,
  "drivers": ["Positive sentiment +0.65", "Low inventory scarcity premium", "Competitor anchor: ₹24,750"]
}
```
