from __future__ import annotations

import pandas as pd

POSITIVE_WORDS = {"great", "good", "excellent", "fast", "value", "love", "smooth", "amazing"}
NEGATIVE_WORDS = {"bad", "poor", "slow", "hate", "issue", "defect", "broken", "delay"}


def sentiment_score(reviews: pd.DataFrame, sku: str) -> float:
    sku_reviews = reviews[reviews["sku"] == sku].copy()
    if sku_reviews.empty:
        return 0.5

    rating_score = sku_reviews["rating"].mean() / 5.0

    def lexical_score(text: str) -> float:
        words = {w.strip(".,!").lower() for w in text.split()}
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        if pos + neg == 0:
            return 0.5
        return (pos + 1) / (pos + neg + 2)

    lex_scores = sku_reviews["review_text"].fillna("").apply(lexical_score)
    return float(0.6 * rating_score + 0.4 * lex_scores.mean())
