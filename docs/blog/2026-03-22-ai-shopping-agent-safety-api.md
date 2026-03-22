# How AI Shopping Agents Can Use CIRE for Real-Time Ingredient Safety

If your shopping agent recommends skincare products, it needs a safety layer.

CIRE provides deterministic INCI risk scoring so an AI agent can:
1. Parse ingredient lists
2. Score safety risk consistently
3. Filter out high-risk items before recommendation

## Integration pattern
- Product ingest → extract INCI
- Call `POST /v1/analyze`
- Apply policy threshold (e.g. moderate+ only)
- Return shortlist with confidence score

## Why deterministic matters
Agent ecosystems need repeatable outputs. CIRE is rule-based (no stochastic generation), so the same input returns the same JSON result.

## 30-second example
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/analyze \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci":"Water, Retinol, Glycolic Acid"}'
```

## Best practice
Use `POST /v1/batch` for catalog ingestion and nightly refresh.

---

CIRE docs: https://web-production-9cdb4.up.railway.app/docs
