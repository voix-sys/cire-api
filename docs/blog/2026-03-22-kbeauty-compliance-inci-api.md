# K-Beauty Export Compliance: Why INCI API Filtering Should Come First

K-beauty teams expanding to global marketplaces face a common issue:
manual ingredient review does not scale.

CIRE helps by turning INCI strings into structured risk signals:
- irritation
- allergen
- pregnancy
- acne
- interaction

## Compliance-first workflow
1. Pull ingredient lists from catalog
2. Run `POST /v1/batch`
3. Flag risky SKUs for manual/legal review
4. Approve safe candidates for channel listing

## Benefits
- Faster screening for large catalogs
- Consistent policy enforcement
- Better audit trail in downstream systems

## Example call
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/batch \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci_list":["Water, Niacinamide","Water, Retinol, Salicylic Acid"]}'
```

---

API docs: https://web-production-9cdb4.up.railway.app/docs
