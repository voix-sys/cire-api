# CIRE Pro Formulation Intelligence — Execution Plan (2026-03-21)

## Goal
Move CIRE from risk-only API to subscription value API:
- `synergy_score` (beneficial pairs)
- `conflict_score` (risky/irritating combinations)
- `optimal_formulation` (goal-based ingredient suggestions)

## Subscription Value Ladder
- Free: `/v1/analyze` only
- Pro: `/v1/synergy`, `/v1/optimal`
- Enterprise: custom rules, regional compliance packs, audit logs

## Immediate Build Scope (Phase 1)
1. Data tables
   - `ingredient_pairs`
   - `formulation_goals`
   - `evidence_refs`
2. Endpoints
   - `POST /v1/synergy`
   - `POST /v1/optimal`
3. Billing
   - Pro-only access gate by API key tier
4. Evidence model
   - each recommendation includes source + evidence_level

## Data Source Strategy (No Brave required)
Primary sources:
- PubMed E-utilities
- Europe PMC
- Crossref/OpenAlex metadata
Secondary sources:
- Dermatology society guidelines
- Technical ingredient monographs
Tertiary sources:
- product-level review patterns (tagged low-confidence)

## Evidence Levels
- A: Meta-analysis / RCT / consensus guideline
- B: Controlled/observational clinical evidence
- C: Mechanistic or in vitro support
- D: Expert/opinion/review-derived signal

## First Milestones
- M1 (today): schema + endpoint contract draft
- M2 (today): seed 20+ evidence rows from public APIs
- M3 (next): implement endpoint logic + deterministic scorer
- M4 (next): package as Pro feature and document pricing behavior
