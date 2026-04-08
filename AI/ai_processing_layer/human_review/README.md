# Human Review Module

Ensures all AI recommendations pass through appropriate human approval before execution.

## Approach (To Implement)

### Workflow
1. AI generates recommendation (price change, stock order, risk alert)
2. Recommendation queued for human review with full explanation
3. Reviewer approves, modifies, or rejects
4. Decision logged with audit trail (who, when, why, original vs modified)

### Review Tiers
| Decision Type | Auto-Approve Threshold | Requires Review |
|--------------|----------------------|----------------|
| Price change < 3% | confidence > 0.85 | No |
| Price change 3-10% | Always | Category Manager |
| Price change > 10% | Always | Director |
| Stock order < ₹1L | confidence > 0.80 | No |
| Stock order > ₹1L | Always | Supply Chain Lead |
| Risk alert (critical) | Never auto-approve | Risk Committee |

### Audit Trail Fields
- Decision ID, timestamp, reviewer, original recommendation
- Modification details, final decision, rationale
- Model version, data snapshot hash
