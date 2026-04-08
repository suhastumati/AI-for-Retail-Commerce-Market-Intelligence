from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Recommendation:
    sku: str
    product: str
    brand: str
    current_price: float
    recommended_price: float
    recommended_discount_pct: float
    expected_monthly_demand: int
    expected_monthly_profit: float
    confidence: float
    drivers: List[str]
    risks: List[str]
    sentiment_score: float
    market_summary: str
    metadata: Dict[str, str]

    def to_dict(self) -> Dict:
        return {
            "sku": self.sku,
            "product": self.product,
            "brand": self.brand,
            "current_price": round(self.current_price, 2),
            "recommended_price": round(self.recommended_price, 2),
            "recommended_discount_pct": round(self.recommended_discount_pct, 2),
            "expected_monthly_demand": int(self.expected_monthly_demand),
            "expected_monthly_profit": round(self.expected_monthly_profit, 2),
            "confidence": round(self.confidence, 2),
            "drivers": self.drivers,
            "risks": self.risks,
            "sentiment_score": round(self.sentiment_score, 3),
            "market_summary": self.market_summary,
            "metadata": self.metadata,
        }
