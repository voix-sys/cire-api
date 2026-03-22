# CIRE Pro: From Risk Scoring to Formulation Intelligence

Risk scoring is the baseline. Pro users need guidance.

CIRE Pro adds:
- `POST /v1/synergy`: beneficial vs risky ingredient pair scoring
- `POST /v1/optimal`: goal-based ingredient recommendations

## Pro use cases
- R&D assistant co-pilot
- formulation candidate ranking
- safety-aware innovation workflows

## Example (synergy)
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/synergy \
  -H "X-API-Key: PRO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci":"Water, Adapalene, Benzoyl Peroxide"}'
```

## Example (optimal)
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/optimal \
  -H "X-API-Key: PRO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci":"Water, Niacinamide","goal":"acne"}'
```

Free tier keys return 403 on Pro endpoints by design.

---

Docs: https://web-production-9cdb4.up.railway.app/docs
