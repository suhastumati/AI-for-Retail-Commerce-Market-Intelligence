"""
Comprehensive Analytics Engine for Retail Intelligence Platform.
Computes all metrics from existing project datasets — no synthetic data.
"""
from __future__ import annotations
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Lazy imports for new modules (avoid circular / missing dep crashes) ───────
def _demand_forecast_module():
    try:
        from . import demand_forecasting as df_mod
        return df_mod
    except ImportError:
        try:
            import demand_forecasting as df_mod
            return df_mod
        except ImportError:
            return None

def _news_events_module():
    try:
        from . import news_events as ne_mod
        return ne_mod
    except ImportError:
        try:
            import news_events as ne_mod
            return ne_mod
        except ImportError:
            return None

def _profit_engine_module():
    try:
        from . import profit_engine as pe_mod
        return pe_mod
    except ImportError:
        try:
            import profit_engine as pe_mod
            return pe_mod
        except ImportError:
            return None

def _live_data_module():
    try:
        from . import live_data_fetcher as ld_mod
        return ld_mod
    except ImportError:
        try:
            import live_data_fetcher as ld_mod
            return ld_mod
        except ImportError:
            return None

def _competitor_scraper_module():
    try:
        from . import competitor_scraper as cs_mod
        return cs_mod
    except ImportError:
        try:
            import competitor_scraper as cs_mod
            return cs_mod
        except ImportError:
            return None

# ---------------------------------------------------------------------------
# SKU → Product metadata (for the 6 review-only SKUs that lack sales rows)
# ---------------------------------------------------------------------------
SKU_META = {
    "TV-IND-001": {"name": "Smart TV 55\"",         "brand": "Samsung",    "cat": "Electronics"},
    "MB-IND-002": {"name": "Smartphone Pro",          "brand": "Apple",      "cat": "Mobile"},
    "LP-IND-003": {"name": "Laptop Ultra",            "brand": "Dell",       "cat": "Computing"},
    "WM-IND-004": {"name": "Washing Machine 7kg",     "brand": "LG",         "cat": "Appliances"},
    "AC-IND-005": {"name": "Air Conditioner 1.5T",    "brand": "Daikin",     "cat": "Appliances"},
    "HP-IND-006": {"name": "Headphones Pro",          "brand": "Sony",       "cat": "Audio"},
    "TB-IND-007": {"name": "Tablet 10\"",             "brand": "Xiaomi",     "cat": "Computing"},
    "RF-IND-008": {"name": "Refrigerator 300L",       "brand": "Whirlpool",  "cat": "Appliances"},
}

ASPECT_KEYWORDS = {
    "quality":     ["quality", "build", "material", "durable", "sturdy", "finish"],
    "price":       ["price", "cost", "expensive", "cheap", "value", "worth", "affordable"],
    "battery":     ["battery", "charge", "charging", "power", "backup"],
    "camera":      ["camera", "photo", "picture", "image", "video", "lens"],
    "display":     ["display", "screen", "resolution", "brightness", "color"],
    "performance": ["performance", "speed", "fast", "slow", "lag", "processor"],
    "design":      ["design", "look", "sleek", "heavy", "light", "compact"],
    "service":     ["service", "support", "warranty", "repair", "response"],
    "delivery":    ["delivery", "shipping", "packaging", "arrived", "dispatch"],
    "sound":       ["sound", "audio", "speaker", "bass", "volume"],
}


class RetailAnalytics:
    """Computes all dashboard metrics from project CSVs."""

    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.sales       = data.get("sales",       pd.DataFrame())
        self.reviews     = data.get("reviews",     pd.DataFrame())
        self.competitors = data.get("competitors", pd.DataFrame())
        self.weather     = data.get("weather",     pd.DataFrame())
        self.events      = data.get("events",      pd.DataFrame())
        self.festivals   = data.get("festivals",   pd.DataFrame())
        self.sentiment   = data.get("sentiment",   pd.DataFrame())
        # Real external datasets (from live_data_fetcher / data_loader)
        self.wiki_views  = data.get("wiki_views",  pd.DataFrame())
        self.cpi         = data.get("cpi",         pd.DataFrame())
        self.gdelt       = data.get("gdelt",       pd.DataFrame())
        self._ensure_dates()
        self._collect_skus()

    # ── helpers ───────────────────────────────────────────────────────────
    def _ensure_dates(self):
        for attr in ("sales", "reviews", "competitors", "weather",
                     "events", "festivals", "sentiment"):
            df = getattr(self, attr)
            if not df.empty and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

    def _collect_skus(self):
        skus = set()
        for df in (self.sales, self.reviews, self.sentiment):
            if not df.empty and "sku" in df.columns:
                skus.update(df["sku"].unique())
        self.all_skus = sorted(skus)

    @staticmethod
    def _safe(v):
        if isinstance(v, (np.integer,)):   return int(v)
        if isinstance(v, (np.floating,)):  return float(v)
        if isinstance(v, (np.bool_,)):     return bool(v)
        if pd.isna(v):                     return None
        return v

    # ── products ──────────────────────────────────────────────────────────
    def get_products(self) -> List[Dict]:
        products = []
        for sku in self.all_skus:
            meta = SKU_META.get(sku, {"name": sku, "brand": "—", "cat": "—"})
            # Sales
            ss = self.sales[self.sales["sku"] == sku] if not self.sales.empty else pd.DataFrame()
            has_sales = not ss.empty
            if has_sales:
                latest = ss.sort_values("date").iloc[-1]
                total_rev   = float((ss["price"] * ss["units_sold"]).sum())
                total_units = int(ss["units_sold"].sum())
                cur_price   = float(latest["price"])
                cur_cost    = float(latest["cost"])
                latest_sold = int(latest["units_sold"])
                avg_margin  = float(((ss["price"] - ss["cost"]) / ss["price"] * 100).mean())
            else:
                total_rev = total_units = cur_price = cur_cost = latest_sold = 0
                avg_margin = 0.0

            # Sentiment
            sdf = self.sentiment
            if not sdf.empty and "sku" in sdf.columns:
                ss_sent = sdf[sdf["sku"] == sku]
                if not ss_sent.empty and "sentiment_unified" in ss_sent.columns:
                    avg_sent = float(ss_sent["sentiment_unified"].mean())
                    review_ct = len(ss_sent)
                else:
                    avg_sent, review_ct = 0.5, 0
            else:
                revs = self.reviews[self.reviews["sku"] == sku] if not self.reviews.empty else pd.DataFrame()
                avg_sent = float(revs["rating"].mean() / 5) if not revs.empty else 0.5
                review_ct = len(revs)

            avg_rating = 0.0
            if not self.reviews.empty:
                rr = self.reviews[self.reviews["sku"] == sku]
                if not rr.empty:
                    avg_rating = float(rr["rating"].mean())

            # Competitor
            cc = self.competitors[self.competitors["sku"] == sku] if not self.competitors.empty else pd.DataFrame()
            comp_avg = float(cc["price"].mean()) if not cc.empty else 0

            products.append({
                "sku": sku,
                "product": meta["name"],
                "brand": meta["brand"],
                "category": meta["cat"],
                "current_price": round(cur_price),
                "current_cost": round(cur_cost),
                "total_revenue": round(total_rev),
                "total_units": total_units,
                "latest_units": latest_sold,
                "avg_margin": round(avg_margin, 1),
                "avg_sentiment": round(avg_sent, 3),
                "avg_rating": round(avg_rating, 2),
                "review_count": review_ct,
                "competitor_avg": round(comp_avg),
                "has_sales": has_sales,
                "has_competitor": not cc.empty,
            })
        return sorted(products, key=lambda x: x["total_revenue"], reverse=True)

    # ── dashboard KPIs ────────────────────────────────────────────────────
    def dashboard_kpis(self) -> Dict:
        s = self.sales
        if s.empty:
            return {}
        s = s.copy()
        s["revenue"] = s["price"] * s["units_sold"]
        s["margin"]  = (s["price"] - s["cost"]) / s["price"] * 100

        total_rev = float(s["revenue"].sum())
        avg_margin = float(s["margin"].mean())
        latest_units = int(s.sort_values("date").groupby("sku")["units_sold"].last().sum())

        # sentiment across all reviews
        if not self.sentiment.empty and "sentiment_unified" in self.sentiment.columns:
            avg_sent = float(self.sentiment["sentiment_unified"].mean())
        else:
            avg_sent = 0.5

        # simple trend: compare last 12 rows vs previous 12
        sorted_s = s.sort_values("date")
        mid = len(sorted_s) // 2
        rev_prev = sorted_s.iloc[:mid]["revenue"].sum()
        rev_recent = sorted_s.iloc[mid:]["revenue"].sum()
        rev_change = ((rev_recent - rev_prev) / rev_prev * 100) if rev_prev else 0

        margin_prev = sorted_s.iloc[:mid]["margin"].mean()
        margin_recent = sorted_s.iloc[mid:]["margin"].mean()
        margin_change = margin_recent - margin_prev

        return {
            "total_revenue": {"value": round(total_rev), "change": round(rev_change, 1), "period": "vs prior period"},
            "avg_margin":    {"value": round(avg_margin, 1), "change": round(margin_change, 1), "period": "pp vs prior"},
            "total_units":   {"value": int(s["units_sold"].sum()), "latest_monthly": latest_units},
            "avg_sentiment": {"value": round(avg_sent, 3), "change": 0},
        }

    # ── revenue trend ─────────────────────────────────────────────────────
    def revenue_trend(self) -> Dict:
        if self.sales.empty:
            return {"dates": [], "revenue": [], "margin": [], "units": []}
        s = self.sales.copy().sort_values("date")
        s["revenue"] = s["price"] * s["units_sold"]
        s["margin"]  = (s["price"] - s["cost"]) / s["price"] * 100
        monthly = s.groupby(s["date"].dt.to_period("M")).agg(
            revenue=("revenue", "sum"),
            margin=("margin", "mean"),
            units=("units_sold", "sum"),
        ).reset_index()
        monthly["date"] = monthly["date"].dt.to_timestamp()
        return {
            "dates":   [d.strftime("%Y-%m") for d in monthly["date"]],
            "revenue": [round(v) for v in monthly["revenue"]],
            "margin":  [round(v, 1) for v in monthly["margin"]],
            "units":   [int(v) for v in monthly["units"]],
        }

    # ── alerts ────────────────────────────────────────────────────────────
    def generate_alerts(self) -> List[Dict]:
        alerts = []
        products = self.get_products()
        for p in products:
            if not p["has_sales"]:
                continue
            sku, name = p["sku"], p["product"]
            # inventory proxy
            dio = p["latest_units"] / max(1, p["total_units"] / 72) * 30
            if dio < 10:
                alerts.append({
                    "severity": "critical",
                    "sku": sku, "product": name,
                    "message": f"Low stock alert — estimated {dio:.0f} days of inventory",
                    "action": f"Order {int(p['latest_units']*1.5)} units (≈₹{int(p['latest_units']*1.5*p['current_cost']):,})",
                })
            # sentiment negative
            if p["avg_sentiment"] < 0.4:
                alerts.append({
                    "severity": "high",
                    "sku": sku, "product": name,
                    "message": f"Sentiment dropped to {p['avg_sentiment']:.2f} — investigate reviews",
                    "action": "Review recent negative feedback and take corrective action",
                })
            # competitor undercut
            if p["has_competitor"] and p["competitor_avg"] > 0:
                gap = (p["current_price"] - p["competitor_avg"]) / p["competitor_avg"] * 100
                if gap > 5:
                    alerts.append({
                        "severity": "high",
                        "sku": sku, "product": name,
                        "message": f"Price {gap:.1f}% above competitor average (₹{p['competitor_avg']:,})",
                        "action": f"Consider reducing price by ≈{gap/2:.0f}%",
                    })
            # margin erosion
            if p["avg_margin"] < 20:
                alerts.append({
                    "severity": "medium",
                    "sku": sku, "product": name,
                    "message": f"Margin at {p['avg_margin']:.1f}% — below 20% threshold",
                    "action": "Review cost structure or raise prices",
                })
        # event alerts
        if not self.events.empty:
            for _, ev in self.events.iterrows():
                if float(ev.get("impact_score", 0)) > 0.5:
                    alerts.append({
                        "severity": "medium",
                        "sku": "ALL", "product": "All Products",
                        "message": f"Supply chain event: {ev.get('summary', 'Unknown')}",
                        "action": "Adjust demand forecasts and review inventory buffers",
                    })
        # sort by severity order
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(alerts, key=lambda a: sev_order.get(a["severity"], 9))

    # ── pricing analysis ──────────────────────────────────────────────────
    def pricing_analysis(self) -> List[Dict]:
        # ── Fetch live event-based price signals once (shared across all SKUs) ──
        event_signals: Dict = {}
        try:
            ld_mod = _live_data_module()
            if ld_mod:
                event_signals = ld_mod.get_event_price_signals()
        except Exception as e:
            logger.warning(f"Event price signals unavailable: {e}")

        results = []
        for sku in self.all_skus:
            ss = self.sales[self.sales["sku"] == sku] if not self.sales.empty else pd.DataFrame()
            if ss.empty:
                continue
            meta = SKU_META.get(sku, {"name": sku})
            latest = ss.sort_values("date").iloc[-1]
            price = float(latest["price"])
            cost  = float(latest["cost"])

            # elasticity (log-log, detrended to remove spurious time correlation)
            if len(ss) > 10:
                ss_s = ss.sort_values("date").copy()
                # Remove linear time trend from both log-price and log-demand
                t = np.arange(len(ss_s), dtype=float)
                lp_raw = np.log(ss_s["price"].values)
                ld_raw = np.log(ss_s["units_sold"].values.clip(min=1))
                lp = lp_raw - np.polyval(np.polyfit(t, lp_raw, 1), t)
                ld = ld_raw - np.polyval(np.polyfit(t, ld_raw, 1), t)
                coef = np.polyfit(lp, ld, 1)
                elasticity = float(np.clip(coef[0], -3.5, -0.3))  # economics: always negative
            else:
                elasticity = -1.2

            # competitor data
            cc = self.competitors[self.competitors["sku"] == sku] if not self.competitors.empty else pd.DataFrame()
            comp_avg = float(cc.sort_values("date").tail(6)["price"].mean()) if not cc.empty else price

            # sentiment modifier
            sdf = self.sentiment
            if not sdf.empty and "sku" in sdf.columns:
                sk = sdf[sdf["sku"] == sku]
                sent = float(sk["sentiment_unified"].mean()) if "sentiment_unified" in sk.columns and not sk.empty else 0.5
            else:
                sent = 0.5
            sent_mod = 1 + (sent - 0.5) * 0.1   # ±5% around neutral

            # optimal price via fine-grained grid search (±20%, competitor-bounded)
            avg_demand = float(ss["units_sold"].mean())
            best_price, best_profit, best_demand = price, 0.0, avg_demand

            # Upper ceiling: max(current, competitor_avg) * 1.05 — don't go too far above market
            price_ceiling = max(price, comp_avg) * 1.05
            price_floor   = cost * 1.10  # minimum 10% margin

            fine_pcts = list(range(-20, 22, 2))  # -20% to +20% in 2% steps
            for pct in fine_pcts:
                p = price * (1 + pct / 100)
                if p < price_floor or p > price_ceiling:
                    continue
                d = max(1, avg_demand * (p / price) ** elasticity * sent_mod)
                # Apply competitor penalty: if p > 5% above comp_avg, demand drops more
                if comp_avg > 0 and p > comp_avg * 1.05:
                    comp_penalty = ((p / comp_avg) - 1.05) * 2  # extra elasticity penalty
                    d = d * max(0.5, 1 - comp_penalty)
                profit = (p - cost) * d
                if profit > best_profit:
                    best_profit = profit
                    best_price  = p
                    best_demand = d

            # Build sensitivity table for chart (7 display points)
            sensitivity = []
            for pct in [-10, -6, -3, 0, 3, 6, 10]:
                p = price * (1 + pct / 100)
                d = max(1, avg_demand * (p / price) ** elasticity * sent_mod)
                profit = (p - cost) * d
                rev    = p * d
                label  = "Current" if pct == 0 else ""
                sensitivity.append({
                    "price": round(p), "demand": round(d),
                    "revenue": round(rev), "profit": round(profit), "label": label,
                })

            # mark recommended in sensitivity table
            for s in sensitivity:
                if abs(s["price"] - round(best_price)) <= price * 0.04:
                    if s["label"] == "":
                        s["label"] = "Recommended ★"

            change_pct = (best_price - price) / price * 100
            opt_margin = (best_price - cost) / best_price * 100
            cur_profit = (price - cost) * avg_demand
            profit_change = ((best_profit - cur_profit) / cur_profit * 100) if cur_profit else 0

            # ── Apply live event signals to final recommendation ───────────────
            event_adj_pct   = float(event_signals.get("net_adjustment_pct", 0))
            event_direction = event_signals.get("direction", "hold")
            event_summary   = event_signals.get("summary", "")
            top_signals     = event_signals.get("signals", [])

            # Nudge best_price by event signal (capped at ±5% additional adjustment)
            event_nudge = float(np.clip(event_adj_pct, -5, 5))
            event_adjusted_price = best_price * (1 + event_nudge / 100)
            # Re-clamp to cost floor + competitor ceiling
            event_adjusted_price = float(np.clip(
                event_adjusted_price, cost * 1.10, max(price, comp_avg) * 1.10
            ))
            if abs(event_nudge) >= 0.5:
                best_price  = event_adjusted_price
                change_pct  = (best_price - price) / price * 100
                opt_margin  = (best_price - cost) / best_price * 100

            # ── Build rationale ───────────────────────────────────────────────
            rationale = []
            if sent > 0.6: rationale.append(f"Strong positive sentiment ({sent:.2f}) → premium pricing supported")
            if sent < 0.4: rationale.append(f"Negative sentiment ({sent:.2f}) — careful raising prices")
            if comp_avg > price * 1.02:
                rationale.append(f"Competitors priced higher (+₹{comp_avg - price:,.0f}) → room to increase")
            elif comp_avg < price * 0.98:
                rationale.append(f"Competitors priced lower (−₹{price - comp_avg:,.0f}) → price pressure")
            rationale.append(f"Elasticity {elasticity:.2f} — {'inelastic: price changes barely affect demand' if abs(elasticity) < 1 else 'elastic: price-sensitive market'}")

            # Event-derived rationale (most impactful first)
            if top_signals:
                rationale.append(f"📰 Live market signal ({event_direction.upper()}): {event_summary}")
                for sig in top_signals[:2]:
                    rationale.append(f"  • {sig['title'][:70]} → {sig['reason']}")

            risk_checks = [
                {"check": f"Margin at optimal: {opt_margin:.1f}% > 15%",    "pass": opt_margin > 15},
                {"check": f"Price change: {abs(change_pct):.1f}% < 10%",    "pass": abs(change_pct) < 10},
                {"check": f"Competitor variance: {abs(best_price-comp_avg)/comp_avg*100:.1f}% < 8%",
                 "pass": abs(best_price-comp_avg)/comp_avg*100 < 8 if comp_avg else True},
            ]

            results.append({
                "sku": sku,
                "product": meta["name"],
                "brand":   meta.get("brand", ""),
                "category": meta.get("cat", "Electronics"),
                "current_price": round(price),
                "recommended_price": round(best_price),
                "change_pct": round(change_pct, 1),
                "elasticity": round(elasticity, 3),
                "competitor_avg": round(comp_avg),
                "sentiment": round(sent, 3),
                "current_demand": round(avg_demand),
                "optimal_demand": round(best_demand) if best_profit > 0 else round(avg_demand),
                "current_profit": round(cur_profit),
                "optimal_profit": round(best_profit),
                "profit_change_pct": round(profit_change, 1),
                "margin_at_optimal": round(opt_margin, 1),
                "rationale": rationale,
                "risk_checks": risk_checks,
                "sensitivity": sensitivity,
                "event_price_signal": {
                    "direction":       event_direction,
                    "adjustment_pct":  round(event_adj_pct, 2),
                    "summary":         event_summary,
                    "top_signals":     top_signals[:3],
                },
                "status": "Optimized",
            })
        return results

    # ── inventory analysis ────────────────────────────────────────────────
    def inventory_analysis(self) -> List[Dict]:
        results = []
        lead_time = 14  # days
        for sku in self.all_skus:
            ss = self.sales[self.sales["sku"] == sku] if not self.sales.empty else pd.DataFrame()
            if ss.empty:
                continue
            meta = SKU_META.get(sku, {"name": sku})
            latest = ss.sort_values("date").iloc[-1]
            avg_monthly = float(ss["units_sold"].mean())
            daily_demand = avg_monthly / 30
            current_stock = int(latest["units_sold"] * 1.2)
            dio = current_stock / daily_demand if daily_demand > 0 else 999
            safety_stock = daily_demand * lead_time * 0.5
            reorder_point = daily_demand * lead_time + safety_stock
            # EOQ
            order_cost = 5000
            holding_cost = float(latest["cost"]) * 0.02 * 12
            eoq = np.sqrt(2 * avg_monthly * 12 * order_cost / max(1, holding_cost))
            stockout_prob = max(0, 1 - current_stock / max(1, avg_monthly)) * 100

            if dio < lead_time:
                urgency = "critical"
                order_qty = int(eoq * 1.5)
            elif dio < lead_time + 7:
                urgency = "warning"
                order_qty = int(eoq)
            elif dio > 30:
                urgency = "overstock"
                order_qty = 0
            else:
                urgency = "optimal"
                order_qty = 0

            results.append({
                "sku": sku,
                "product": meta["name"],
                "current_stock": current_stock,
                "daily_demand": round(daily_demand),
                "dio": round(dio, 1),
                "target_dio": 10,
                "reorder_point": round(reorder_point),
                "safety_stock": round(safety_stock),
                "eoq": round(eoq),
                "order_qty": order_qty,
                "order_cost": round(order_qty * float(latest["cost"])),
                "stockout_prob": round(stockout_prob, 1),
                "urgency": urgency,
                "avg_monthly_demand": round(avg_monthly),
            })
        return results

    # ── sentiment analysis ────────────────────────────────────────────────
    def sentiment_overview(self) -> Dict:
        sdf = self.sentiment if not self.sentiment.empty else self.reviews
        if sdf.empty:
            return {}

        per_sku = {}
        for sku in self.all_skus:
            sk = sdf[sdf["sku"] == sku]
            if sk.empty:
                continue
            meta = SKU_META.get(sku, {"name": sku})

            if "sentiment_unified" in sk.columns:
                avg_s = float(sk["sentiment_unified"].mean())
            elif "rating" in sk.columns:
                avg_s = float(sk["rating"].mean() / 5)
            else:
                avg_s = 0.5

            avg_r = float(sk["rating"].mean()) if "rating" in sk.columns else 0
            count = len(sk)

            # Emotion breakdown (from JSON column)
            emotions = {}
            if "emotion_labels" in sk.columns:
                for emo_str in sk["emotion_labels"].dropna():
                    for em in str(emo_str).split(","):
                        em = em.strip().strip("[]'\" ")
                        if em:
                            emotions[em] = emotions.get(em, 0) + 1

            # Aspect-based sentiment from review text
            aspects = {}
            if "review_text" in sk.columns:
                for _, row in sk.iterrows():
                    text = str(row.get("review_text", "")).lower()
                    for aspect, keywords in ASPECT_KEYWORDS.items():
                        if any(kw in text for kw in keywords):
                            if aspect not in aspects:
                                aspects[aspect] = {"mentions": 0, "total_rating": 0}
                            aspects[aspect]["mentions"] += 1
                            aspects[aspect]["total_rating"] += float(row.get("rating", 3))

            aspect_list = []
            for asp, vals in aspects.items():
                avg_rating_asp = vals["total_rating"] / vals["mentions"] if vals["mentions"] > 0 else 3
                score = (avg_rating_asp - 3) / 2  # normalise to ~-1..+1
                aspect_list.append({
                    "aspect": asp,
                    "sentiment": round(score, 2),
                    "mentions": vals["mentions"],
                    "status": "Strength" if score > 0.2 else ("Weakness" if score < -0.2 else "Watch"),
                })
            aspect_list.sort(key=lambda x: x["sentiment"], reverse=True)

            # fraud stats
            fraud_pct = 0
            if "fraud_flag_v2" in sk.columns:
                fraud_pct = float(sk["fraud_flag_v2"].mean()) * 100
            elif "fraud_flag" in sk.columns:
                fraud_pct = float(sk["fraud_flag"].mean()) * 100

            # sarcasm
            sarcasm_pct = 0
            if "sarcastic" in sk.columns:
                sarcasm_pct = float(sk["sarcastic"].mean()) * 100
            elif "sarcasm_label" in sk.columns:
                sarcasm_pct = float((sk["sarcasm_label"].str.lower() == "irony").mean()) * 100

            per_sku[sku] = {
                "sku": sku,
                "product": meta["name"],
                "avg_sentiment": round(avg_s, 3),
                "avg_rating": round(avg_r, 2),
                "review_count": count,
                "top_emotions": dict(sorted(emotions.items(), key=lambda x: -x[1])[:8]),
                "aspects": aspect_list[:10],
                "fraud_pct": round(fraud_pct, 1),
                "sarcasm_pct": round(sarcasm_pct, 1),
            }

        # Recent reviews
        recent = []
        rev_df = self.reviews if not self.reviews.empty else pd.DataFrame()
        if not rev_df.empty:
            for _, r in rev_df.sort_values("date", ascending=False).head(20).iterrows():
                meta = SKU_META.get(r.get("sku", ""), {"name": r.get("sku", "")})
                recent.append({
                    "sku": r.get("sku"),
                    "product": meta["name"],
                    "rating": int(r.get("rating", 0)),
                    "text": str(r.get("review_text", ""))[:200],
                    "date": str(r.get("date", ""))[:10],
                })

        # overall emotion aggregation
        all_emotions = {}
        for sk_data in per_sku.values():
            for em, ct in sk_data["top_emotions"].items():
                all_emotions[em] = all_emotions.get(em, 0) + ct
        top_emotions = dict(sorted(all_emotions.items(), key=lambda x: -x[1])[:10])

        return {
            "per_sku": per_sku,
            "recent_reviews": recent,
            "overall_emotions": top_emotions,
            "overall_avg": round(np.mean([v["avg_sentiment"] for v in per_sku.values()]), 3) if per_sku else 0.5,
        }

    # ── competitor analysis ───────────────────────────────────────────────
    def competitor_analysis(self) -> Dict:
        if self.competitors.empty:
            return {"products": []}

        products = []
        for sku in self.competitors["sku"].unique():
            meta = SKU_META.get(sku, {"name": sku})
            cc = self.competitors[self.competitors["sku"] == sku].sort_values("date")
            ss = self.sales[self.sales["sku"] == sku].sort_values("date") if not self.sales.empty else pd.DataFrame()
            our_price = float(ss["price"].iloc[-1]) if not ss.empty else 0

            # Per-competitor breakdown
            competitors_detail = []
            for comp in cc["competitor"].unique():
                comp_data = cc[cc["competitor"] == comp].sort_values("date")
                latest_p = float(comp_data["price"].iloc[-1])
                trend_data = comp_data.tail(12)
                if len(trend_data) > 1:
                    pct_change = (float(trend_data["price"].iloc[-1]) - float(trend_data["price"].iloc[0])) / float(trend_data["price"].iloc[0]) * 100
                else:
                    pct_change = 0
                competitors_detail.append({
                    "name": comp,
                    "latest_price": round(latest_p),
                    "trend_pct": round(pct_change, 1),
                    "position": "Below" if latest_p < our_price else "Above",
                    "prices": [round(float(p)) for p in comp_data["price"].tolist()[-24:]],
                    "dates":  [d.strftime("%Y-%m") for d in comp_data["date"].tolist()[-24:]],
                })

            comp_avg = float(cc.tail(12)["price"].mean())
            gap_pct = ((our_price - comp_avg) / comp_avg * 100) if comp_avg else 0

            # Our price history
            our_prices = [round(float(p)) for p in ss["price"].tolist()[-24:]] if not ss.empty else []
            our_dates  = [d.strftime("%Y-%m") for d in ss["date"].tolist()[-24:]] if not ss.empty else []

            products.append({
                "sku": sku,
                "product": meta["name"],
                "our_price": round(our_price),
                "competitor_avg": round(comp_avg),
                "gap_pct": round(gap_pct, 1),
                "position": "Premium" if gap_pct > 2 else ("Discount" if gap_pct < -2 else "Parity"),
                "competitors": competitors_detail,
                "our_prices": our_prices,
                "our_dates": our_dates,
            })

        # Competitor news from events
        news = []
        if not self.events.empty:
            for _, ev in self.events.sort_values("date", ascending=False).head(10).iterrows():
                news.append({
                    "date": str(ev.get("date", ""))[:10],
                    "summary": str(ev.get("summary", "")),
                    "impact": float(ev.get("impact_score", 0)),
                    "type": str(ev.get("event_type", "")),
                })

        return {"products": products, "news": news}

    # ── sales time-series per SKU ─────────────────────────────────────────
    def sales_timeseries(self, sku: str) -> Dict:
        ss = self.sales[self.sales["sku"] == sku].sort_values("date") if not self.sales.empty else pd.DataFrame()
        if ss.empty:
            return {}
        return {
            "dates":  [d.strftime("%Y-%m") for d in ss["date"]],
            "prices": [round(float(p)) for p in ss["price"]],
            "costs":  [round(float(c)) for c in ss["cost"]],
            "units":  [int(u) for u in ss["units_sold"]],
            "revenue":[round(float(p*u)) for p, u in zip(ss["price"], ss["units_sold"])],
        }

    # ── sentiment trend over time ─────────────────────────────────────────
    def sentiment_trend(self, sku: str = None) -> Dict:
        sdf = self.sentiment if not self.sentiment.empty else self.reviews
        if sdf.empty:
            return {"dates": [], "values": []}
        if sku:
            sdf = sdf[sdf["sku"] == sku]
        if sdf.empty:
            return {"dates": [], "values": []}

        sdf = sdf.copy()
        if "sentiment_unified" in sdf.columns:
            col = "sentiment_unified"
        elif "rating" in sdf.columns:
            sdf["_sent"] = sdf["rating"] / 5
            col = "_sent"
        else:
            return {"dates": [], "values": []}

        monthly = sdf.groupby(sdf["date"].dt.to_period("M"))[col].mean().reset_index()
        monthly["date"] = monthly["date"].dt.to_timestamp()
        return {
            "dates":  [d.strftime("%Y-%m") for d in monthly["date"]],
            "values": [round(float(v), 3) for v in monthly[col]],
        }

    # ── festival data ─────────────────────────────────────────────────────
    def festival_impacts(self) -> List[Dict]:
        if self.festivals.empty:
            return []
        return [
            {"date": str(r["date"])[:10],
             "festival": str(r.get("festival", "")),
             "impact": float(r.get("impact_factor", 0))}
            for _, r in self.festivals.iterrows()
        ]

    # ── demand forecasting ────────────────────────────────────────────────────
    def demand_forecast(self, sku: Optional[str] = None, horizon_weeks: int = 8) -> Any:
        """Generate demand forecasts using the ensemble forecasting module."""
        df_mod = _demand_forecast_module()
        if df_mod is None:
            return [] if sku is None else {}
        # Pass real external datasets (wiki views + CPI from data_loader)
        wiki_views = getattr(self, 'wiki_views', pd.DataFrame())
        cpi_data   = getattr(self, 'cpi',        pd.DataFrame())
        if sku:
            return df_mod.generate_demand_forecast(
                sku=sku, sales=self.sales, festivals=self.festivals,
                events=self.events, competitors=self.competitors,
                sentiment=self.sentiment, horizon_weeks=horizon_weeks,
                wiki_views=wiki_views, cpi_data=cpi_data,
            )
        return df_mod.forecast_all_skus(
            sales=self.sales, festivals=self.festivals, events=self.events,
            competitors=self.competitors, sentiment=self.sentiment,
            horizon_weeks=horizon_weeks, wiki_views=wiki_views, cpi_data=cpi_data,
        )

    # ── news & events aggregator ──────────────────────────────────────────────
    def news_events_aggregated(self) -> Dict:
        """
        Aggregate news events.
        Now defaults to LIVE data (GDELT direct CSV + python-holidays + World Bank).
        No API keys required — all sources are genuinely free and open.
        Falls back to static CSV only if live fetch completely fails.
        """
        ld_mod = _live_data_module()
        if ld_mod is not None:
            try:
                return ld_mod.get_live_events_feed(limit=60)
            except Exception as e:
                logger.warning(f"Live data fetch failed, falling back to static: {e}")

        # Fallback: static events CSV enrichment via old news_events module
        ne_mod = _news_events_module()
        if ne_mod is not None:
            try:
                return ne_mod.aggregate_events(events_df=self.events, use_live_api=False)
            except Exception:
                pass

        # Last resort: bare static events
        static_events = []
        if not self.events.empty:
            for _, r in self.events.iterrows():
                static_events.append({
                    "title": str(r.get("summary", "")),
                    "published_at": str(r.get("date", ""))[:10],
                    "event_type": str(r.get("event_type", "unknown")).lower(),
                    "source": "Internal Dataset (fallback)",
                    "demand_change_pct": round(float(r.get("impact_score", 0)) * -20, 1),
                    "direction": "negative",
                    "duration_days": 30,
                    "confidence": 0.7,
                    "raw_impact_score": float(r.get("impact_score", 0)),
                })
        return {
            "events": static_events,
            "summary": {
                "total_events": len(static_events),
                "high_impact_count": sum(1 for e in static_events if abs(e.get("demand_change_pct", 0)) > 8),
                "net_negative_impact_pct": 0, "net_positive_impact_pct": 0, "by_type": {},
            },
            "data_sources": ["Internal Dataset (fallback)"],
            "sources_detail": {},
            "last_updated": datetime.now().isoformat(),
            "api_keys_required": False,
        }

    # ── profit margin engine ──────────────────────────────────────────────────
    def profit_margins(self) -> Dict:
        """Full cost-stack margin analysis for all SKUs."""
        pe_mod = _profit_engine_module()
        products = self.get_products()
        if pe_mod is None:
            results = []
            for p in products:
                if not p.get("has_sales"):
                    continue
                price = float(p["current_price"])
                cost  = float(p["current_cost"])
                if price == 0:
                    continue
                margin_pct = (price - cost) / price * 100
                results.append({
                    "sku": p["sku"], "product": p["product"],
                    "price": round(price), "cogs": round(cost),
                    "margin_pct": round(margin_pct, 1),
                    "margin_status": "healthy" if margin_pct >= 20 else "tight",
                    "period_revenue": round(price * p.get("latest_units", 0)),
                    "period_profit": round((price - cost) * p.get("latest_units", 0)),
                    "breakdown": [],
                })
            total_rev = sum(r["period_revenue"] for r in results)
            total_pft = sum(r["period_profit"] for r in results)
            return {
                "by_sku": results,
                "portfolio_margin_pct": round(total_pft / total_rev * 100, 1) if total_rev else 0,
                "total_period_revenue": round(total_rev),
                "total_period_profit": round(total_pft),
                "below_threshold_count": sum(1 for r in results if r["margin_pct"] < 20),
                "improvement_opportunities": [],
            }
        return pe_mod.portfolio_margin_overview(products, self.sales)

    def profit_scenario(self, sku: str) -> Dict:
        """Run what-if price scenario analysis for a single SKU."""
        pe_mod = _profit_engine_module()
        if pe_mod is None:
            return {}
        products = self.get_products()
        product = next((p for p in products if p["sku"] == sku), None)
        if not product or not product.get("has_sales"):
            return {}
        sku_to_category = {
            "TV-IND-001": "Electronics", "MB-IND-002": "Mobile",
            "LP-IND-003": "Computing",   "WM-IND-004": "Appliances",
            "AC-IND-005": "Appliances",  "HP-IND-006": "Audio",
            "TB-IND-007": "Computing",   "RF-IND-008": "Appliances",
        }
        pricing = self.pricing_analysis()
        pa = next((p for p in pricing if p["sku"] == sku), None)
        elasticity = pa["elasticity"] if pa else -1.2
        ss = self.sales[self.sales["sku"] == sku].sort_values("date") if not self.sales.empty else pd.DataFrame()
        avg_demand = float(ss["units_sold"].mean()) if not ss.empty else 100
        inventory = self.inventory_analysis()
        inv = next((i for i in inventory if i["sku"] == sku), None)
        inventory_days = inv["dio"] if inv else 15.0
        return pe_mod.price_scenario_analysis(
            base_price=float(product["current_price"]),
            cogs=float(product["current_cost"]),
            avg_demand=avg_demand,
            elasticity=elasticity,
            sentiment_score=float(product["avg_sentiment"]),
            competitor_avg=float(product["competitor_avg"]) or float(product["current_price"]),
            inventory_days=inventory_days,
            category=sku_to_category.get(sku, "Electronics"),
        )

    # ── live competitor price monitor ─────────────────────────────────────────
    def live_competitor_prices(self) -> Dict:
        """Fetch live / simulated competitor prices for all portfolio SKUs."""
        cs_mod = _competitor_scraper_module()
        products = self.get_products()
        if cs_mod is None:
            return {"live_prices": [], "alerts": [], "price_map": {}, "monitored_at": datetime.now().isoformat()}
        return cs_mod.monitor_all_prices(products, self.competitors)
