# AI Business Copilot Module

Conversational interface for business users to query insights, run what-if scenarios, and get explanations.

## Approach (To Implement)

### Architecture
- **Foundation Model**: AWS Bedrock (Claude/Titan) or open-source (Llama 3)
- **Grounding**: RAG over structured analytics outputs (demand forecasts, pricing, sentiment)
- **Prompts**: Domain-specific system prompts with retail context

### Capabilities
1. **Natural Language Queries**: "Why did we recommend a price increase for TV-IND-001?"
2. **What-If Scenarios**: "What happens to profit if we lower price by 10%?"
3. **Comparative Analysis**: "How does this SKU's sentiment compare to last quarter?"
4. **Alert Explanation**: "Why was a risk alert triggered today?"

### Integration
- Reads from all module outputs (sentiment, demand, pricing, risk)
- Grounds responses in actual data, not hallucinations
- Links to source evidence (reviews, news articles, competitor data)
