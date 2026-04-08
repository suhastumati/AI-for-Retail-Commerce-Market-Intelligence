# Explainability Module

Provides transparent, auditable explanations for all AI-driven decisions (pricing, inventory, risk alerts).

## Approach (To Implement)

### Techniques
1. **SHAP (SHapley Additive exPlanations)** — Feature attribution for tree/neural models
2. **LIME (Local Interpretable Model-agnostic Explanations)** — Local surrogate explanations
3. **Permutation Importance** — Feature importance via performance degradation
4. **Counterfactual Explanations** — "What would need to change for a different decision?"

### Application to Each Module

| Module | Explanation Type | Example |
|--------|-----------------|---------|
| Demand Forecast | Feature importance | "Festival season contributed +30% to demand estimate" |
| Pricing | Decision waterfall | "Base price ₹25K → +₹1K (low inventory) → -₹500 (competitor) = ₹25,500" |
| Risk | Event attribution | "Port strike in Chennai: 0.72 severity, affects TV supply chain" |
| Sentiment | Aspect attribution | "Camera aspect: +0.8, Battery aspect: -0.3, Overall: +0.65" |

### Libraries
- `shap` — SHAP values for XGBoost, LightGBM, neural networks
- `lime` — LIME explanations
- `eli5` — Permutation importance
- `alibi` — Counterfactual explanations

### Output
Natural language explanation + visual waterfall chart for every recommendation.
