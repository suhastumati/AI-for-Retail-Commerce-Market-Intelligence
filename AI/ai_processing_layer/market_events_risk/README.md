# Market Events & Risk Intelligence Module

Detects and quantifies the demand impact of geopolitical events, news, regulatory changes, and competitor moves.

## Approach (To Implement)

### Data Sources (All Free)

| Source | Coverage | API | Update |
|--------|----------|-----|--------|
| **GDELT Project** | 250M+ events, 65 languages | BigQuery (free tier) | Every 15 min |
| **NewsAPI** | 50k+ sources, 75 countries | REST (100 req/day free) | Real-time |
| **GNews** | Google News aggregation | REST (free) | Real-time |
| **python-holidays** | 100+ countries festivals | Python package | Static |
| **Wikipedia pageviews** | Public interest proxy | REST (free) | Daily |

### Event Classification Pipeline

1. **Data Collection** — Fetch from multiple APIs every 6 hours
2. **Deduplication** — SimHash to remove duplicate articles
3. **Relevance Filtering** — Keyword + NER + cosine similarity (threshold > 0.7)
4. **Impact Classification** — BERT-based multi-label classifier:
   - Event type: recall, competitor launch, regulation, supply chain, positive media
   - Sentiment: -1 to +1
   - Severity: 0 to 1

### Event Types & Impact

| Event Type | Keywords | Demand Impact | Timeframe |
|-----------|----------|--------------|-----------|
| Product Recall | "recall", "defect", "safety" | -40% to -70% | 3-5 days |
| Competitor Launch | "launch", "new product" | -10% to -25% | 2-4 weeks |
| Supply Chain Disruption | "port strike", "chip shortage" | Stock-out risk | 1-6 weeks |
| Regulatory Change | "tariff", "GST", "import duty" | Cost +5-20% | Immediate |
| Positive Media | "award", "best product" | +15-30% | 2-4 weeks |
| Negative Media | "poor quality", "avoid" | -8-15% | 1-2 weeks |

### Integration with Other Modules
- Adjust demand forecast based on detected events
- Re-trigger pricing optimization on high-severity alerts
- Feed risk scores into human review queue

### Output
```json
{
  "event_id": "evt_2026_0401_001",
  "type": "regulatory_change",
  "title": "New 20% import duty on electronics",
  "severity": 0.85,
  "sentiment": -0.6,
  "estimated_demand_impact": -0.15,
  "affected_skus": ["TV-IND-001"],
  "recommended_action": "Raise price 8-12% to offset cost increase",
  "source_urls": ["https://..."],
  "detected_at": "2026-04-01T06:00:00Z"
}
```
