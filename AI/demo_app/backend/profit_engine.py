"""
Profit Margin Calculation Engine.

Full cost-stack breakdown:
  COGS → Logistics → Platform Fees → Marketing → Overhead → Contingency

Outputs:
  - Per-unit and per-SKU margin breakdown
  - Scenario analysis (price ±10%)
  - Sentiment-adjusted pricing with margin floor guardrails
  - What-if decision matrix (sentiment × inventory × competitor)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# ── Default Cost Structure (% of selling price, configurable per category) ──

DEFAULT_COST_STRUCTURE = {
    "Electronics": {
        "cogs_pct": 0.48,            # 48% raw cost
        "logistics_pct": 0.06,        # 6% shipping/warehouse
        "platform_fee_pct": 0.05,     # 5% Amazon/Flipkart fee
        "payment_gateway_pct": 0.02,  # 2% Razorpay/CCAvenue
        "marketing_pct": 0.04,        # 4% ads + promos
        "operational_pct": 0.03,      # 3% salaries, infra
        "contingency_pct": 0.02,      # 2% shrinkage, returns
    },
    "Mobile": {
        "cogs_pct": 0.50,
        "logistics_pct": 0.04,
        "platform_fee_pct": 0.06,
        "payment_gateway_pct": 0.02,
        "marketing_pct": 0.05,
        "operational_pct": 0.03,
        "contingency_pct": 0.02,
    },
    "Computing": {
        "cogs_pct": 0.52,
        "logistics_pct": 0.05,
        "platform_fee_pct": 0.05,
        "payment_gateway_pct": 0.02,
        "marketing_pct": 0.03,
        "operational_pct": 0.03,
        "contingency_pct": 0.02,
    },
    "Appliances": {
        "cogs_pct": 0.45,
        "logistics_pct": 0.08,
        "platform_fee_pct": 0.04,
        "payment_gateway_pct": 0.02,
        "marketing_pct": 0.04,
        "operational_pct": 0.04,
        "contingency_pct": 0.02,
    },
    "Audio": {
        "cogs_pct": 0.42,
        "logistics_pct": 0.04,
        "platform_fee_pct": 0.06,
        "payment_gateway_pct": 0.02,
        "marketing_pct": 0.06,
        "operational_pct": 0.03,
        "contingency_pct": 0.02,
    },
}

# Minimum acceptable margins (by category)
MIN_MARGINS = {
    "Electronics": 0.15,
    "Mobile": 0.12,
    "Computing": 0.12,
    "Appliances": 0.18,
    "Audio": 0.20,
    "default": 0.15,
}


# ── Core Cost Breakdown ───────────────────────────────────────────────────────

def compute_cost_breakdown(
    selling_price: float,
    cogs: float,
    category: str = "Electronics",
) -> Dict[str, Any]:
    """
    Compute full cost breakdown for a single unit at a given selling price.

    Args:
        selling_price: Current / target selling price (₹)
        cogs: Actual cost of goods (from sales.csv cost column)
        category: Product category for variable cost %

    Returns:
        {components: [{name, amount, pct}], total_cost, gross_margin, net_margin, margin_pct}
    """
    struct = DEFAULT_COST_STRUCTURE.get(category, DEFAULT_COST_STRUCTURE["Electronics"])

    components = [
        {
            "name": "Cost of Goods (COGS)",
            "amount": round(cogs),
            "pct": round(cogs / selling_price * 100, 1),
            "type": "fixed",
        },
        {
            "name": "Logistics & Fulfillment",
            "amount": round(selling_price * struct["logistics_pct"]),
            "pct": round(struct["logistics_pct"] * 100, 1),
            "type": "variable",
        },
        {
            "name": "Platform Fee (Marketplace)",
            "amount": round(selling_price * struct["platform_fee_pct"]),
            "pct": round(struct["platform_fee_pct"] * 100, 1),
            "type": "variable",
        },
        {
            "name": "Payment Gateway",
            "amount": round(selling_price * struct["payment_gateway_pct"]),
            "pct": round(struct["payment_gateway_pct"] * 100, 1),
            "type": "variable",
        },
        {
            "name": "Marketing & Promotions",
            "amount": round(selling_price * struct["marketing_pct"]),
            "pct": round(struct["marketing_pct"] * 100, 1),
            "type": "semi_variable",
        },
        {
            "name": "Operational Overhead",
            "amount": round(selling_price * struct["operational_pct"]),
            "pct": round(struct["operational_pct"] * 100, 1),
            "type": "fixed",
        },
        {
            "name": "Contingency & Returns",
            "amount": round(selling_price * struct["contingency_pct"]),
            "pct": round(struct["contingency_pct"] * 100, 1),
            "type": "variable",
        },
    ]

    total_variable = sum(c["amount"] for c in components[1:])  # exclude COGS
    total_cost = cogs + total_variable
    gross_margin = selling_price - cogs
    net_margin = selling_price - total_cost
    margin_pct = net_margin / selling_price * 100 if selling_price > 0 else 0

    return {
        "selling_price": round(selling_price),
        "cogs": round(cogs),
        "components": components,
        "total_variable_cost": round(total_variable),
        "total_cost": round(total_cost),
        "gross_margin": round(gross_margin),
        "gross_margin_pct": round(gross_margin / selling_price * 100, 1) if selling_price > 0 else 0,
        "net_margin": round(net_margin),
        "margin_pct": round(margin_pct, 1),
        "margin_status": _margin_status(margin_pct, category),
        "min_viable_price": round(total_cost / (1 - MIN_MARGINS.get(category, 0.15))),
    }


def _margin_status(margin_pct: float, category: str) -> str:
    min_m = MIN_MARGINS.get(category, MIN_MARGINS["default"]) * 100
    if margin_pct < min_m:
        return "below_threshold"
    if margin_pct < min_m + 5:
        return "tight"
    if margin_pct < min_m + 15:
        return "healthy"
    return "excellent"


# ── Price Scenario Analysis ──────────────────────────────────────────────────

def price_scenario_analysis(
    base_price: float,
    cogs: float,
    avg_demand: float,
    elasticity: float,
    sentiment_score: float,
    competitor_avg: float,
    inventory_days: float,
    category: str = "Electronics",
    price_steps_pct: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Run a what-if scenario analysis across price points.

    Incorporates:
    - Price elasticity (demand response)
    - Sentiment multiplier (willingness-to-pay adjustment)
    - Inventory scarcity multiplier (low stock → price power)
    - Competitor anchor (max premium above market)

    Returns optimal price, scenario table, and decision rationale.
    """
    if price_steps_pct is None:
        price_steps_pct = [-15, -10, -6, -3, 0, 3, 6, 10, 15]

    # Modifiers
    # Sentiment: each 0.1 above neutral (0.5) allows 1% price premium
    sentiment_mod = 1 + (sentiment_score - 0.5) * 0.10

    # Inventory: DIO < 10 days → scarcity premium, DIO > 30 → discount pressure
    if inventory_days < 7:
        inventory_mod = 1.06   # +6% scarcity
    elif inventory_days < 14:
        inventory_mod = 1.02   # +2%
    elif inventory_days > 45:
        inventory_mod = 0.94   # -6% overstock discount
    elif inventory_days > 30:
        inventory_mod = 0.97   # -3%
    else:
        inventory_mod = 1.0

    struct = DEFAULT_COST_STRUCTURE.get(category, DEFAULT_COST_STRUCTURE["Electronics"])
    variable_cost_pct = (
        struct["logistics_pct"] + struct["platform_fee_pct"] +
        struct["payment_gateway_pct"] + struct["marketing_pct"] +
        struct["operational_pct"] + struct["contingency_pct"]
    )
    min_viable = cogs / (1 - variable_cost_pct - MIN_MARGINS.get(category, 0.15))

    # Competitor ceiling: don't price more than 10% above competitor avg.
    # But ensure the ceiling is always at least min_viable + 5% — otherwise
    # no scenarios are generated when costs are high relative to competitors.
    raw_ceiling = competitor_avg * 1.10 if competitor_avg > 0 else base_price * 1.20
    max_price = max(raw_ceiling, min_viable * 1.05, base_price * 1.20)

    # Also extend price_steps to cover the full viable range
    if price_steps_pct is None:
        price_steps_pct = [-15, -10, -6, -3, 0, 3, 6, 10, 15]
    # Ensure current price (0%) and extremes are always included
    pct_range = sorted(set(price_steps_pct + [-15, -10, -5, 0, 5, 10, 15, 20]))

    scenarios: List[Dict] = []
    best_scenario: Optional[Dict] = None
    best_profit = -1e9

    for pct in pct_range:
        candidate_price = base_price * (1 + pct / 100)

        # Clamp to viable range — use soft lower bound (warn but include)
        if candidate_price > max_price:
            continue
        if candidate_price < cogs * 1.02:  # absolute floor: must cover COGS
            continue

        # Demand = avg_demand × (price/base)^elasticity × sentiment_mod × inventory_mod
        price_ratio = candidate_price / base_price
        demand = max(1, avg_demand * (price_ratio ** elasticity) * sentiment_mod * inventory_mod)

        breakdown = compute_cost_breakdown(candidate_price, cogs, category)
        unit_profit = breakdown["net_margin"]
        total_profit = unit_profit * demand
        total_revenue = candidate_price * demand
        margin_pct = breakdown["margin_pct"]

        competitor_gap = (candidate_price - competitor_avg) / competitor_avg * 100 if competitor_avg > 0 else 0

        scenario = {
            "price_change_pct": pct,
            "price": round(candidate_price),
            "demand": round(demand, 1),
            "unit_margin": round(unit_profit),
            "margin_pct": round(margin_pct, 1),
            "total_profit": round(total_profit),
            "total_revenue": round(total_revenue),
            "competitor_gap_pct": round(competitor_gap, 1),
            "viable": margin_pct >= MIN_MARGINS.get(category, 0.15) * 100,
            "label": "Current" if pct == 0 else "",
        }
        scenarios.append(scenario)

        if total_profit > best_profit and scenario["viable"]:
            best_profit = total_profit
            best_scenario = scenario

    # Label best
    if best_scenario:
        for s in scenarios:
            if s["price"] == best_scenario["price"] and s["label"] == "":
                s["label"] = "Recommended ★"

    # Build decision rationale
    rationale = _build_rationale(
        sentiment_score, inventory_days, competitor_avg, base_price,
        elasticity, best_scenario
    )

    # Decision matrix cell
    matrix_cell = _decision_matrix_cell(sentiment_score, inventory_days, competitor_avg, base_price)

    return {
        "base_price": round(base_price),
        "recommended_price": best_scenario["price"] if best_scenario else round(base_price),
        "price_change_pct": best_scenario["price_change_pct"] if best_scenario else 0,
        "sentiment_modifier": round(sentiment_mod, 3),
        "inventory_modifier": round(inventory_mod, 3),
        "competitor_ceiling": round(max_price),
        "min_viable_price": round(min_viable),
        "scenarios": scenarios,
        "best_scenario": best_scenario,
        "rationale": rationale,
        "decision_matrix_cell": matrix_cell,
        "current_breakdown": compute_cost_breakdown(base_price, cogs, category),
        "optimal_breakdown": compute_cost_breakdown(
            best_scenario["price"] if best_scenario else base_price, cogs, category
        ),
    }


def _build_rationale(
    sentiment: float, inventory_days: float, comp_avg: float,
    our_price: float, elasticity: float, best: Optional[Dict],
) -> List[str]:
    reasons = []

    if sentiment > 0.65:
        reasons.append(f"High positive sentiment ({sentiment:.2f}) → customers willing to pay premium")
    elif sentiment > 0.5:
        reasons.append(f"Moderate positive sentiment ({sentiment:.2f}) → market pricing supported")
    elif sentiment < 0.35:
        reasons.append(f"Negative sentiment ({sentiment:.2f}) → aggressive pricing may be needed")

    if inventory_days < 10:
        reasons.append(f"Low inventory ({inventory_days:.0f} days) → scarcity premium applicable")
    elif inventory_days > 30:
        reasons.append(f"High inventory ({inventory_days:.0f} days) → discount to accelerate turnover")

    if comp_avg > 0:
        gap_pct = (our_price - comp_avg) / comp_avg * 100
        if gap_pct > 5:
            reasons.append(f"We are {gap_pct:.1f}% above competitor average → price pressure")
        elif gap_pct < -5:
            reasons.append(f"We are {abs(gap_pct):.1f}% below competitor average → room to increase")
        else:
            reasons.append(f"Competitive parity (+{gap_pct:.1f}% vs market) → hold position")

    if abs(elasticity) < 1:
        reasons.append(f"Inelastic demand (ε={elasticity:.2f}) → price increases don't hurt volume much")
    else:
        reasons.append(f"Elastic demand (ε={elasticity:.2f}) → price-sensitive; be cautious raising")

    if best:
        profit_pct = (best["price_change_pct"])
        direction = "raise" if profit_pct > 0 else ("lower" if profit_pct < 0 else "maintain")
        reasons.append(
            f"Optimal action: {direction} price by {abs(profit_pct):.0f}% "
            f"→ maximises total profit at ₹{best['total_profit']:,}/period"
        )

    return reasons


def _decision_matrix_cell(
    sentiment: float, inventory_days: float, comp_avg: float, our_price: float
) -> Dict[str, str]:
    """
    The 3-dimensional decision matrix:
    [Sentiment: High/Med/Low] × [Inventory: Low/Med/High] × [vs Competitor: Above/Parity/Below]
    """
    sent_tier = "high" if sentiment > 0.6 else ("low" if sentiment < 0.4 else "medium")
    inv_tier  = "low" if inventory_days < 10 else ("high" if inventory_days > 30 else "medium")
    comp_gap  = (our_price - comp_avg) / comp_avg * 100 if comp_avg > 0 else 0
    comp_tier = "above" if comp_gap > 3 else ("below" if comp_gap < -3 else "parity")

    # Decision rules
    actions = {
        ("high", "low", "parity"):   ("Raise Price 8-15%",  "Demand high, supply low, market neutral"),
        ("high", "low", "above"):    ("Hold or Raise 3-5%", "Strong demand, limited stock, premium pos."),
        ("high", "low", "below"):    ("Raise to Parity",    "Opportunity to capture margin"),
        ("high", "medium", "parity"):("Raise 3-6%",         "Positive sentiment supports premium"),
        ("high", "medium", "above"): ("Hold Current",       "Premium justified by sentiment"),
        ("high", "medium", "below"): ("Raise 5-8%",         "High sentiment + room to grow margin"),
        ("high", "high", "parity"):  ("Hold or Raise 3%",   "Good sentiment but stock pressure"),
        ("high", "high", "above"):   ("Consider −3 to −5%", "Move excess stock despite good sentiment"),
        ("high", "high", "below"):   ("Raise 5-8%",         "Overstock but below market — balance"),
        ("medium", "low", "parity"): ("Raise 3-6%",         "Scarcity premium available"),
        ("medium", "low", "above"):  ("Hold Current",       "Don't risk further premium with neutral sent."),
        ("medium", "low", "below"):  ("Raise to Parity",    "Below market + low stock = raise"),
        ("medium", "medium", "any"): ("Hold Current",       "No strong signal either way"),
        ("medium", "high", "parity"):("Lower 3-5%",         "Move stock, neutral sentiment"),
        ("medium", "high", "above"): ("Lower 5-8%",         "High stock + premium = move inventory"),
        ("medium", "high", "below"): ("Hold or slight −2%", "Already below market, just hold"),
        ("low", "low", "parity"):    ("Hold — Investigate", "Mixed signals: fix quality issues first"),
        ("low", "medium", "parity"): ("Lower 5-8%",         "Negative sentiment requires discount"),
        ("low", "high", "parity"):   ("Lower 10-15%",       "Negative sentiment + overstock = clear"),
        ("low", "high", "above"):    ("Lower 15-20%",        "Critical — fix quality AND clear stock"),
        ("low", "any", "below"):     ("Lower 3-5% + fix",   "Already cheap, focus on fixing issues"),
    }

    key = (sent_tier, inv_tier, comp_tier)
    fallback_key = (sent_tier, inv_tier, "any")
    action_data = actions.get(key) or actions.get(fallback_key) or ("Hold Current", "Insufficient signal")

    return {
        "sentiment_tier": sent_tier,
        "inventory_tier": inv_tier,
        "competitor_tier": comp_tier,
        "action": action_data[0],
        "rationale": action_data[1],
    }


# ── Portfolio Margin Overview ─────────────────────────────────────────────────

def portfolio_margin_overview(
    products: List[Dict],
    sales: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Compute full margin overview for all SKUs.

    products: from analytics.get_products()
    sales: raw sales DataFrame
    """
    sku_to_category = {
        "TV-IND-001": "Electronics",
        "MB-IND-002": "Mobile",
        "LP-IND-003": "Computing",
        "WM-IND-004": "Appliances",
        "AC-IND-005": "Appliances",
        "HP-IND-006": "Audio",
        "TB-IND-007": "Computing",
        "RF-IND-008": "Appliances",
    }

    results = []
    total_revenue = 0
    total_profit = 0

    for p in products:
        sku = p["sku"]
        if not p.get("has_sales"):
            continue

        category = sku_to_category.get(sku, "Electronics")
        price = float(p["current_price"])
        cogs  = float(p["current_cost"])

        if price == 0:
            continue

        breakdown = compute_cost_breakdown(price, cogs, category)
        monthly_units = float(p.get("latest_units", p.get("avg_monthly_demand", 0)))

        period_revenue = price * monthly_units
        period_profit  = breakdown["net_margin"] * monthly_units

        total_revenue += period_revenue
        total_profit  += period_profit

        results.append({
            "sku": sku,
            "product": p["product"],
            "category": category,
            "price": round(price),
            "cogs": round(cogs),
            "net_margin_per_unit": breakdown["net_margin"],
            "margin_pct": breakdown["margin_pct"],
            "margin_status": breakdown["margin_status"],
            "total_cost_per_unit": breakdown["total_cost"],
            "gross_margin_pct": breakdown["gross_margin_pct"],
            "period_revenue": round(period_revenue),
            "period_profit": round(period_profit),
            "units": round(monthly_units),
            "min_viable_price": breakdown["min_viable_price"],
            "breakdown": breakdown["components"],
        })

    # Sort by period profit descending
    results.sort(key=lambda x: x["period_profit"], reverse=True)

    portfolio_margin = total_profit / total_revenue * 100 if total_revenue > 0 else 0

    # Improvement opportunities
    opportunities = []
    for r in results:
        if r["margin_pct"] < 20:
            gain_per_unit = r["price"] * 0.03  # 3% price lift
            opportunities.append({
                "sku": r["sku"],
                "product": r["product"],
                "issue": f"Margin {r['margin_pct']:.1f}% below 20% threshold",
                "suggestion": f"Raise price by 3% → +₹{round(gain_per_unit)}/unit",
                "potential_gain": round(gain_per_unit * r["units"]),
            })

    return {
        "by_sku": results,
        "portfolio_margin_pct": round(portfolio_margin, 1),
        "total_period_revenue": round(total_revenue),
        "total_period_profit": round(total_profit),
        "below_threshold_count": sum(1 for r in results if r["margin_pct"] < 20),
        "improvement_opportunities": opportunities,
    }
