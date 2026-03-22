# CIRE API — Cosmetic Ingredient Risk Engine

[![CIRE Certified](https://img.shields.io/badge/CIRE-Certified-brightgreen)](https://web-production-9cdb4.up.railway.app)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)]()
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

## Tier Behavior

- **Free tier API key**: can call `/v1/analyze`, `/v1/credits`, billing/account endpoints
- **Pro tier API key**: includes Free endpoints + `/v1/synergy` and `/v1/optimal`
- Calling Pro endpoints with a Free key returns:
  - `403 Forbidden`
  - clear message: `Pro tier required for this endpoint...`

---

## API Reference

Full interactive docs: [/docs](https://web-production-9cdb4.up.railway.app/docs)

### `POST /v1/analyze`
Analyze an INCI string. Costs 1 credit.

### `POST /v1/synergy` *(Pro tier)*
Deterministic pair scoring for beneficial and risky combinations.

Request:
```json
{ "inci": "Water, Adapalene, Benzoyl Peroxide" }
```

Response includes:
- `synergy_score`
- `conflict_score`
- `evidence_level`
- `evidence_refs`

### `POST /v1/optimal` *(Pro tier)*
Goal-based deterministic recommendation endpoint.

Request:
```json
{ "inci": "Water, Niacinamide", "goal": "acne" }
```

Response includes:
- `recommended_additions`
- `avoid_with_current`
- `evidence_level`
- `evidence_refs`

### `GET /v1/credits`
Check remaining credits and key tier.

## Billing Automation (Paddle)
- `/v1/webhook` handles `transaction.completed` events.
- When `custom_data.credits` is present, credits are added automatically.
- When `custom_data.tier` is `pro`/`enterprise`, API key tier is upgraded automatically.
- Pro subscription checkout package ids supported: `pro_monthly`, `pro_yearly` (requires Paddle price IDs in env).

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
