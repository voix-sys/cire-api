# CIRE Developer Quickstart (AI-Agent Ready)

## What CIRE does
CIRE analyzes cosmetic ingredient lists (INCI) and returns deterministic safety risk JSON.

Best fit:
- AI shopping agents
- product catalog filters
- compliance pipelines
- K-beauty recommendation engines

---

## 1) Get API key
- Register: `POST /v1/register`
- Auth header: `X-API-Key: <your_key>`

```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","name":"your-agent"}'
```

---

## 2) Analyze single INCI
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/analyze \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci":"Water, Retinol, Glycolic Acid"}'
```

---

## 3) Analyze in batch (up to 100)
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/batch \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inci_list":["Water, Glycerin","Water, Retinol, Glycolic Acid"]}'
```

Batch response includes:
- `count`
- `charged_count`
- `error_count`
- `credits_remaining`

---

## 4) Pro endpoints
- `POST /v1/synergy`
- `POST /v1/optimal`

Free keys receive `403` on Pro endpoints.

---

## 5) Endpoint map
- `POST /v1/register`
- `POST /v1/analyze`
- `POST /v1/batch`
- `POST /v1/synergy` (Pro)
- `POST /v1/optimal` (Pro)
- `GET /v1/credits`
- `GET /docs`

---

## SEO/API Discovery keywords
- cosmetic ingredient safety API
- INCI risk scoring API
- K-beauty compliance API
- AI shopping safety filter API
