# CIRE Marketing Plan (Execution) — 2026-03

## 0) Risk Check Gate (must pass before push)
- Service health endpoint returns `version: 0.2.0`
- `/docs` returns HTTP 200
- Free flow: `/v1/register` works and `/v1/analyze` works
- Pro gate: free key to `/v1/synergy` returns 403 with clear message
- No secrets in repo (`ghp_`, `sk-`, `RAILWAY_TOKEN`, `VERCEL_TOKEN`, `GITHUB_TOKEN`)
- Rollback path defined (previous release commit hash)

---

## 1) Positioning (fixed)
**CIRE = Deterministic INCI risk scoring API for AI agents**
- Free: risk scoring (`/v1/analyze`)
- Pro: formulation intelligence (`/v1/synergy`, `/v1/optimal`)
- ICP:
  1. AI shopping/recommendation builders
  2. K-beauty catalog/compliance teams
  3. Indie cosmetic brands / ODM pilot teams

Primary message:
> "From INCI string to production-safe JSON risk decision in one API call."

---

## 2) Channel Plan (2 weeks)

### Week 1 — Launch Surface
1. mcp.so listing submission
2. Product Hunt launch prep package
3. GitHub README conversion upgrade
4. Landing page CTA alignment (`/v1/register` first)

### Week 2 — Pipeline Build
1. B2B pilot outreach list (20 targets)
2. Outbound messages (2 templates)
3. Demo session booking target: 3 meetings
4. Pilot target: 1 paid proof-of-concept

---

## 3) Product Hunt Package (ready-to-use)

## Tagline candidates
1. Deterministic INCI risk API for AI agents
2. Safer beauty recommendations from one INCI string
3. Compliance-ready cosmetic safety scoring API

## One-liner
CIRE turns cosmetic ingredient lists into deterministic safety JSON for AI agents and compliance workflows.

## First comment template
We built CIRE because safety recommendations in beauty are often inconsistent. CIRE gives deterministic, rule-based outputs for risk scoring and now adds Pro formulation intelligence (`/v1/synergy`, `/v1/optimal`) for teams that need explainable decisions.

## Asset checklist
- Hero screenshot (docs + response JSON)
- 20–30s demo GIF (`/v1/register` -> `/v1/analyze`)
- Pro endpoint example screenshot (`/v1/synergy`)
- Pricing card screenshot

---

## 4) B2B Outreach Templates

## Template A (K-beauty exporter)
Subject: INCI safety screening API for export/compliance workflow

Hi {{name}},
We built CIRE, a deterministic INCI safety API for AI and compliance pipelines.
- JSON risk scoring in one call
- explainable category-level outputs
- Pro mode for ingredient synergy/conflict checks
If useful, we can run a 15-minute pilot using your current SKU list.

## Template B (AI product builder)
Subject: Add safety-aware ranking to your beauty recommender

Hi {{name}},
If your app ranks skincare products, CIRE can add deterministic risk signals from raw INCI text.
You can start free, and upgrade to Pro for formulation intelligence endpoints.
Would you like a quick test with your existing product feed?

---

## 5) KPI Dashboard (daily/weekly)
- GitHub: stars, clones
- Landing: visits, conversion to register
- API: `/v1/register` new keys/day
- Revenue: paid conversions / ARPU
- Usage: analyze/synergy/optimal call volume

Threshold alerts
- Visits > 10/day (track source)
- Revenue > $10/day (notify immediately)
- Register spike > 2x baseline

---

## 6) Execution Notes
- External posting/sending (PH, outreach, public messages) requires operator confirmation.
- Keep claim language conservative (deterministic/rule-based, not medical diagnosis).
- Save all campaign decisions in memory + Obsidian.
