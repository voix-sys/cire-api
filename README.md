# CIRE API — Cosmetic Ingredient Risk Engine

[![CIRE Certified](https://img.shields.io/badge/CIRE-Certified-brightgreen)](https://web-production-9cdb4.up.railway.app)
[![Version](https://img.shields.io/badge/version-0.1.1-blue)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

> Deterministic INCI safety scoring API for AI agents.  
> Designed for shopping agents, catalog filters, compliance pipelines, and K-beauty recommendation engines.

---

## What is CIRE?

CIRE scores cosmetic ingredient lists (INCI format) for safety risk across 5 categories:

| Category | Description |
|---|---|
| `irritation_risk` | Skin irritation potential |
| `allergen_risk` | Known allergens |
| `pregnancy_risk` | Ingredients unsafe during pregnancy |
| `acne_risk` | Comedogenic ingredients |
| `interaction_risk` | Dangerous ingredient combinations |

**Fully deterministic. Rule-based. No ML. Always returns valid JSON.**

---

## Quick Start

```bash
curl -X POST https://web-production-9cdb4.up.railway.app/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci": "Water, Retinol, Glycolic Acid"}'
```

**Response:**
```json
{
  "risk_score": 52,
  "risk_level": "moderate",
  "confidence_score": 65,
  "category_results": { ... },
  "matches": { ... }
}
```

- `risk_score`: 0–100 (higher = safer)
- `risk_level`: `low` / `moderate` / `high`
- `confidence_score`: evidence strength (0–100)

---

## Authentication

Pass your API key in the `X-API-Key` header.

```
X-API-Key: cire-xxxxxxxxxxxx
```

Get your API key → [cire.ai](https://web-production-9cdb4.up.railway.app/docs)

---

## Pricing

| Plan | Calls | Price |
|---|---|---|
| Starter | 1,000 | $9 |
| Growth | 10,000 | $49 |
| Scale | 100,000 | $299 |

---

## API Reference

Full interactive docs: [/docs](https://web-production-9cdb4.up.railway.app/docs)

### `POST /v1/analyze`
Analyze an INCI string. Costs 1 credit.

### `GET /v1/credits`
Check remaining credits.

---

## Use Cases

- **Shopping agents** — filter products by pregnancy safety, allergen risk
- **Catalog managers** — bulk scan thousands of SKUs
- **Compliance pipelines** — EU/K-beauty export regulation checks
- **Recommendation engines** — rank products by safety profile

---

## Tech

- Pure Python, zero ML dependencies
- Deterministic outputs — same input always returns same output
- Evidence-based: EU restriction list, FDA advisories, CIR reports, peer-reviewed consensus
- 13/13 smoke tests passing

---

*Built for the AI agent ecosystem. CIRE Certified.*
