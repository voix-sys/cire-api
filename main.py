#!/usr/bin/env python3
"""
CIRE API v0.2 — Cosmetic Ingredient Risk Engine
M2M API for AI agents: pay-per-call + Pro formulation endpoints
"""

import os
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from db import (
    init_db,
    get_key_info,
    deduct_credit,
    log_usage,
    create_key,
    add_credits,
    set_key_tier,
    get_ingredient_pairs,
    get_formulation_goal_rows,
    get_evidence_refs_by_ids,
)
from payments import create_checkout_url, verify_webhook, CREDIT_PACKAGES
from fastapi.middleware.cors import CORSMiddleware

# --- CIRE core import ---
CIRE_DIR = Path(__file__).parent  # same directory as main.py
sys.path.insert(0, str(CIRE_DIR))
from run_cire import compute_result, load_json

# --- Load datasets once at startup ---
INGREDIENT_DATASET = load_json(str(CIRE_DIR / "ingredient_dataset.json"))
INTERACTION_DATASET = load_json(str(CIRE_DIR / "interaction_dataset.json"))

# --- Helpers ---
_WS_RE = re.compile(r"\s+")


def _normalize(s: str) -> str:
    return _WS_RE.sub(" ", s.strip().lower())


def _tokenize_inci(inci: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,;/]", inci) if p.strip()]


def _build_alias_map() -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for rec in INGREDIENT_DATASET:
        canonical = rec["ingredient_name"]
        for name in [canonical] + list(rec.get("aliases", [])):
            n = _normalize(name)
            if n and n not in alias_map:
                alias_map[n] = canonical
    return alias_map


ALIAS_MAP = _build_alias_map()
EVIDENCE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


async def _resolve_evidence_payload(ref_ids: set[int], levels: list[str]) -> tuple[str, list[dict]]:
    refs = await get_evidence_refs_by_ids(sorted(ref_ids))
    if refs:
        levels = levels + [r.get("evidence_level", "D") for r in refs]
    best_level = "D"
    best_rank = 0
    for lv in levels:
        rank = EVIDENCE_RANK.get(str(lv).upper(), 0)
        if rank > best_rank:
            best_rank = rank
            best_level = str(lv).upper()
    return best_level, refs


def _canonical_present_ingredients(inci: str) -> set[str]:
    out: set[str] = set()
    for tok in _tokenize_inci(inci):
        k = _normalize(tok)
        canonical = ALIAS_MAP.get(k)
        if canonical:
            out.add(canonical)
        else:
            out.add(tok.strip())
    return out


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# --- App ---
app = FastAPI(
    title="CIRE API",
    description=(
        "Cosmetic Ingredient Risk Engine — deterministic safety scoring for INCI ingredient lists.\n\n"
        "Designed for AI agents: shopping agents, catalog filters, compliance pipelines, K-beauty recommendation engines.\n\n"
        "**Authentication:** pass your API key in the `X-API-Key` header.\n\n"
        "**Billing:** 1 credit per `/v1/analyze` call.\n"
        "**Pro:** `/v1/synergy` and `/v1/optimal` require Pro tier API key."
    ),
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# --- Models ---
class AnalyzeRequest(BaseModel):
    inci: str  # e.g. "Water, Retinol, Glycolic Acid"


class SynergyRequest(BaseModel):
    inci: str


class OptimalRequest(BaseModel):
    inci: str
    goal: str  # acne | brightening | antiaging | barrier


class BatchAnalyzeRequest(BaseModel):
    inci_list: list[str]


class KeyCreateRequest(BaseModel):
    name: str
    email: str | None = None
    credits: int = 1000


# --- Auth ---
async def get_api_key(key: str = Security(api_key_header)):
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    info = await get_key_info(key)
    if info is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if info["credits"] <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits. Purchase more at https://cire.ai/credits")
    return key


async def get_pro_api_key(key: str = Security(api_key_header)):
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    info = await get_key_info(key)
    if info is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    tier = str(info.get("tier", "free")).lower()
    if tier != "pro":
        raise HTTPException(
            status_code=403,
            detail="Pro tier required for this endpoint. Upgrade your API key tier to access formulation intelligence.",
        )
    return key


# --- Routes ---
@app.get("/", tags=["info"])
def root():
    return {
        "service": "CIRE API",
        "version": "0.2.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /v1/analyze",
            "batch": "POST /v1/batch",
            "synergy": "POST /v1/synergy (pro)",
            "optimal": "POST /v1/optimal (pro)",
            "credits": "GET /v1/credits",
        },
    }


@app.post("/v1/analyze", tags=["core"])
async def analyze(req: AnalyzeRequest, api_key: str = Depends(get_api_key)):
    """
    Analyze an INCI ingredient list and return a safety risk score.

    - **inci**: comma-separated INCI ingredient string
    - Costs **1 credit** per call
    - Returns deterministic JSON — no markdown, no prose
    """
    if not req.inci.strip():
        raise HTTPException(status_code=400, detail="inci must not be empty")

    result = compute_result(req.inci, INGREDIENT_DATASET, INTERACTION_DATASET)

    await deduct_credit(api_key)
    await log_usage(api_key, req.inci, result["risk_level"])

    return result


@app.post("/v1/batch", tags=["core"])
async def analyze_batch(req: BatchAnalyzeRequest, api_key: str = Depends(get_api_key)):
    """Batch analyze endpoint (1 credit per INCI item)."""
    if not req.inci_list:
        raise HTTPException(status_code=400, detail="inci_list must not be empty")
    if len(req.inci_list) > 100:
        raise HTTPException(status_code=400, detail="inci_list supports up to 100 items per request")

    # Pre-flight credit check to avoid partial processing by default
    key_info = await get_key_info(api_key)
    needed = len(req.inci_list)
    remaining = int(key_info.get("credits", 0)) if key_info else 0
    if remaining < needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits for batch. needed={needed}, remaining={remaining}",
        )

    out = []
    for raw in req.inci_list:
        inci = (raw or "").strip()
        if not inci:
            out.append({"error": "inci must not be empty"})
            continue
        result = compute_result(inci, INGREDIENT_DATASET, INTERACTION_DATASET)
        await deduct_credit(api_key)
        await log_usage(api_key, inci, result["risk_level"])
        out.append(result)

    updated = await get_key_info(api_key)
    return {
        "count": len(req.inci_list),
        "results": out,
        "credits_remaining": int(updated.get("credits", 0)) if updated else 0,
    }


@app.post("/v1/synergy", tags=["pro"])
async def synergy(req: SynergyRequest, api_key: str = Depends(get_pro_api_key)):
    """Pro endpoint: deterministic synergy/conflict scoring for an INCI list."""
    if not req.inci.strip():
        raise HTTPException(status_code=400, detail="inci must not be empty")

    present = _canonical_present_ingredients(req.inci)
    pair_rules = await get_ingredient_pairs()

    matched_synergies = []
    matched_conflicts = []
    ref_ids: set[int] = set()
    levels: list[str] = []

    for rule in pair_rules:
        a, b = rule["ingredient_a"], rule["ingredient_b"]
        if a in present and b in present:
            payload = {
                "pair": [a, b],
                "severity": int(rule["severity"]),
                "rationale": rule.get("rationale", ""),
                "evidence_level": rule.get("evidence_level", "D"),
            }
            if rule.get("pair_type") == "synergy":
                matched_synergies.append(payload)
            else:
                matched_conflicts.append(payload)
            if rule.get("evidence_ref_id"):
                ref_ids.add(int(rule["evidence_ref_id"]))
            levels.append(str(rule.get("evidence_level", "D")))

    synergy_points = sum(m["severity"] * 12 for m in matched_synergies)
    conflict_points = sum(m["severity"] * 10 for m in matched_conflicts)
    synergy_score = max(0, min(100, 50 + synergy_points - conflict_points))
    conflict_score = max(0, min(100, sum(m["severity"] * 25 for m in matched_conflicts)))

    evidence_level, evidence_refs = await _resolve_evidence_payload(ref_ids, levels)

    return {
        "synergy_score": synergy_score,
        "conflict_score": conflict_score,
        "present_ingredients": sorted(present),
        "matches": {
            "synergies": matched_synergies,
            "conflicts": matched_conflicts,
        },
        "evidence_level": evidence_level,
        "evidence_refs": evidence_refs,
    }


@app.post("/v1/optimal", tags=["pro"])
async def optimal(req: OptimalRequest, api_key: str = Depends(get_pro_api_key)):
    """Pro endpoint: deterministic goal-based ingredient recommendations."""
    if not req.inci.strip():
        raise HTTPException(status_code=400, detail="inci must not be empty")
    if not req.goal.strip():
        raise HTTPException(status_code=400, detail="goal must not be empty")

    present = _canonical_present_ingredients(req.inci)
    goal_rows = await get_formulation_goal_rows(req.goal.strip().lower())
    if not goal_rows:
        raise HTTPException(
            status_code=400,
            detail="Unsupported goal. Try one of: acne, brightening, antiaging, barrier",
        )

    pair_rules = await get_ingredient_pairs()

    recommendations = []
    avoid_with_current = []
    ref_ids: set[int] = set()
    levels: list[str] = []

    for row in goal_rows:
        name = row["ingredient_name"]
        if name in present:
            continue

        rec = {
            "ingredient_name": name,
            "role": row.get("role", ""),
            "priority": int(row.get("priority", 50)),
            "evidence_level": row.get("evidence_level", "D"),
        }
        recommendations.append(rec)

        if row.get("evidence_ref_id"):
            ref_ids.add(int(row["evidence_ref_id"]))
        levels.append(str(row.get("evidence_level", "D")))

        for rule in pair_rules:
            if rule.get("pair_type") != "conflict":
                continue
            a, b = rule["ingredient_a"], rule["ingredient_b"]
            if (a == name and b in present) or (b == name and a in present):
                avoid_with_current.append(
                    {
                        "recommended": name,
                        "conflicts_with": b if a == name else a,
                        "severity": int(rule["severity"]),
                        "rationale": rule.get("rationale", ""),
                        "evidence_level": rule.get("evidence_level", "D"),
                    }
                )
                if rule.get("evidence_ref_id"):
                    ref_ids.add(int(rule["evidence_ref_id"]))
                levels.append(str(rule.get("evidence_level", "D")))

    recommendations.sort(key=lambda x: (-x["priority"], x["ingredient_name"]))
    evidence_level, evidence_refs = await _resolve_evidence_payload(ref_ids, levels)

    return {
        "goal": req.goal.strip().lower(),
        "present_ingredients": sorted(present),
        "recommended_additions": recommendations[:5],
        "avoid_with_current": avoid_with_current,
        "evidence_level": evidence_level,
        "evidence_refs": evidence_refs,
    }


@app.get("/v1/credits", tags=["account"])
async def credits(api_key: str = Depends(get_api_key)):
    """Check remaining credits for your API key."""
    info = await get_key_info(api_key)
    return {
        "api_key": api_key[:10] + "...",
        "name": info["name"],
        "credits_remaining": info["credits"],
        "tier": info.get("tier", "free"),
    }


class RegisterRequest(BaseModel):
    email: str
    name: str


@app.post("/v1/register", tags=["account"])
async def register(req: RegisterRequest):
    """
    Register a new account. Returns an API key with 100 free credits.
    Use the API key to call /v1/analyze or purchase more credits via /v1/checkout.
    """
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Valid email required")

    key = await create_key(req.name, req.email, credits=100, tier="free")
    return {
        "api_key": key,
        "name": req.name,
        "email": req.email,
        "credits": 100,
        "tier": "free",
        "message": "Welcome to CIRE! You have 100 free credits. Use X-API-Key header to authenticate.",
        "docs": "https://web-production-9cdb4.up.railway.app/docs",
    }


@app.get("/v1/packages", tags=["billing"])
def packages():
    """List available credit packages."""
    return CREDIT_PACKAGES


@app.post("/v1/checkout", tags=["billing"])
async def checkout(package_id: str, api_key: str = Depends(get_api_key)):
    """Create a Paddle checkout URL to purchase credits. Returns URL."""
    base_url = os.environ.get("BASE_URL", "https://web-production-9cdb4.up.railway.app")
    url = create_checkout_url(
        package_id=package_id,
        api_key=api_key,
        success_url=f"{base_url}/v1/checkout/success",
    )
    return {"checkout_url": url}


@app.get("/v1/checkout", tags=["billing"])
async def checkout_redirect(package_id: str, api_key: str):
    """Browser-friendly: redirects directly to Paddle checkout page."""
    base_url = os.environ.get("BASE_URL", "https://web-production-9cdb4.up.railway.app")
    # Validate key manually (no Depends for GET with query param)
    info = await get_key_info(api_key)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    url = create_checkout_url(
        package_id=package_id,
        api_key=api_key,
        success_url=f"{base_url}/v1/checkout/success",
    )
    return RedirectResponse(url=url)


@app.get("/v1/checkout/success", tags=["billing"])
def checkout_success():
    return {"message": "Payment successful! Credits will be added to your account shortly."}


@app.post("/v1/webhook", tags=["billing"], include_in_schema=False)
async def paddle_webhook(request: Request):
    """Paddle webhook — automatically adds credits after payment."""
    payload = await request.body()
    sig_header = request.headers.get("paddle-signature", "")
    event = verify_webhook(payload, sig_header)

    if event.get("event_type") == "transaction.completed":
        custom_data = event.get("data", {}).get("custom_data", {})
        api_key = custom_data.get("api_key")

        # credit top-up
        credits = int(custom_data.get("credits", 0) or 0)
        if api_key and credits > 0:
            await add_credits(api_key, credits)

        # tier upgrade (for Pro subscriptions/packages)
        tier = str(custom_data.get("tier", "")).strip().lower()
        if api_key and tier in {"pro", "enterprise"}:
            await set_key_tier(api_key, tier)

    return {"status": "ok"}


@app.post("/v1/keys", tags=["admin"], include_in_schema=False)
async def issue_key(req: KeyCreateRequest, admin_key: str = Security(api_key_header)):
    """Admin: issue a new API key. Requires admin key."""
    if admin_key != os.environ.get("ADMIN_KEY", ""):  # Set ADMIN_KEY in Railway env vars
        raise HTTPException(status_code=403, detail="Admin only")
    key = await create_key(req.name, req.email, req.credits)
    return {"api_key": key, "name": req.name, "credits": req.credits, "tier": "free"}
