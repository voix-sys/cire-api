#!/usr/bin/env python3
"""
CIRE API v0.1 — Cosmetic Ingredient Risk Engine
M2M API for AI agents: pay-per-call model
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from db import init_db, get_key_info, deduct_credit, log_usage, create_key

# --- CIRE core import ---
CIRE_DIR = Path("/home/k1/.openclaw/skills/cire")
sys.path.insert(0, str(CIRE_DIR))
from run_cire import compute_result, load_json

# --- Load datasets once at startup ---
INGREDIENT_DATASET = load_json(str(CIRE_DIR / "ingredient_dataset.json"))
INTERACTION_DATASET = load_json(str(CIRE_DIR / "interaction_dataset.json"))

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
        "**Billing:** 1 credit per `/v1/analyze` call."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# --- Models ---
class AnalyzeRequest(BaseModel):
    inci: str  # e.g. "Water, Retinol, Glycolic Acid"

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


# --- Routes ---
@app.get("/", tags=["info"])
def root():
    return {
        "service": "CIRE API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /v1/analyze",
            "credits": "GET /v1/credits",
        }
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


@app.get("/v1/credits", tags=["account"])
async def credits(api_key: str = Depends(get_api_key)):
    """Check remaining credits for your API key."""
    info = await get_key_info(api_key)
    return {
        "api_key": api_key[:10] + "...",
        "name": info["name"],
        "credits_remaining": info["credits"],
    }


@app.post("/v1/keys", tags=["admin"], include_in_schema=False)
async def issue_key(req: KeyCreateRequest, admin_key: str = Security(api_key_header)):
    """Admin: issue a new API key. Requires admin key."""
    if admin_key != "test-key-0001":  # TODO: proper admin auth
        raise HTTPException(status_code=403, detail="Admin only")
    key = await create_key(req.name, req.email, req.credits)
    return {"api_key": key, "name": req.name, "credits": req.credits}
