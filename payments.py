"""
payments.py — Paddle integration for CIRE API credit purchases.
"""

import os
import hmac
import hashlib
import json
from fastapi import HTTPException
from paddle_billing import Client, Environment, Options
from paddle_billing.Entities.Shared import TaxCategory
from paddle_billing.Resources.Prices.Operations import CreatePrice
from paddle_billing.Resources.Products.Operations import CreateProduct

PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")

# Sandbox vs Live
PADDLE_ENV = Environment.SANDBOX if os.environ.get("PADDLE_SANDBOX", "false").lower() == "true" else Environment.PRODUCTION

# Credit packages: package_id → { credits, price_usd, name, paddle_price_id }
# paddle_price_id는 Paddle 대시보드에서 생성 후 채워넣어야 함
CREDIT_PACKAGES = {
    "starter": {
        "credits": 1000,
        "price_usd": 9,
        "name": "CIRE Starter — 1,000 calls",
        "paddle_price_id": os.environ.get("PADDLE_PRICE_STARTER", ""),
    },
    "growth": {
        "credits": 10000,
        "price_usd": 49,
        "name": "CIRE Growth — 10,000 calls",
        "paddle_price_id": os.environ.get("PADDLE_PRICE_GROWTH", ""),
    },
    "scale": {
        "credits": 100000,
        "price_usd": 299,
        "name": "CIRE Scale — 100,000 calls",
        "paddle_price_id": os.environ.get("PADDLE_PRICE_SCALE", ""),
    },
    # Pro subscription packages (tier upgrade)
    "pro_monthly": {
        "credits": int(os.environ.get("PADDLE_PRO_MONTHLY_CREDITS", "10000")),
        "price_usd": 29,
        "name": "CIRE Pro Monthly",
        "paddle_price_id": os.environ.get("PADDLE_PRICE_PRO_MONTHLY", ""),
        "tier": "pro",
    },
    "pro_yearly": {
        "credits": int(os.environ.get("PADDLE_PRO_YEARLY_CREDITS", "120000")),
        "price_usd": 290,
        "name": "CIRE Pro Yearly",
        "paddle_price_id": os.environ.get("PADDLE_PRICE_PRO_YEARLY", ""),
        "tier": "pro",
    },
}


def get_paddle_client() -> Client:
    opts = Options(environment=PADDLE_ENV)
    return Client(PADDLE_API_KEY, options=opts)


def create_checkout_url(package_id: str, api_key: str, success_url: str) -> str:
    """Create a Paddle checkout URL."""
    if package_id not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail=f"Unknown package: {package_id}")

    pkg = CREDIT_PACKAGES[package_id]
    price_id = pkg["paddle_price_id"]

    if not price_id:
        raise HTTPException(
            status_code=503,
            detail=f"Package '{package_id}' not configured yet. Contact support."
        )

    # Paddle Checkout URL with custom data (api_key + credits)
    paddle = get_paddle_client()
    custom_data = {
        "api_key": api_key,
        "credits": str(pkg.get("credits", 0)),
        "package_id": package_id,
    }
    if pkg.get("tier"):
        custom_data["tier"] = str(pkg["tier"]).lower()

    transaction = paddle.transactions.create(
        items=[{"price_id": price_id, "quantity": 1}],
        custom_data=custom_data,
    )

    return transaction.checkout["url"]


def verify_webhook(payload: bytes, signature: str) -> dict:
    """Verify Paddle webhook signature and return parsed event."""
    if not PADDLE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    # Paddle uses HMAC-SHA256
    expected = hmac.new(
        PADDLE_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    return json.loads(payload)
