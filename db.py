"""
db.py — SQLite persistence for CIRE API keys and usage logs.
"""

import aiosqlite
import secrets
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "cire.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key         TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT,
                credits     INTEGER NOT NULL DEFAULT 0,
                created_at  INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key     TEXT NOT NULL,
                inci        TEXT NOT NULL,
                risk_level  TEXT,
                called_at   INTEGER NOT NULL
            )
        """)
        # Seed a dev key if table is empty
        async with db.execute("SELECT COUNT(*) FROM api_keys") as cur:
            count = (await cur.fetchone())[0]
        if count == 0:
            await db.execute(
                "INSERT INTO api_keys (key, name, email, credits, created_at) VALUES (?, ?, ?, ?, ?)",
                ("test-key-0001", "dev", None, 9999, int(time.time()))
            )
        await db.commit()


async def get_key_info(key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT key, name, email, credits FROM api_keys WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def deduct_credit(key: str) -> int:
    """Deduct 1 credit. Returns remaining credits."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE api_keys SET credits = credits - 1 WHERE key = ?", (key,)
        )
        await db.commit()
        async with db.execute(
            "SELECT credits FROM api_keys WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def log_usage(key: str, inci: str, risk_level: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_log (api_key, inci, risk_level, called_at) VALUES (?, ?, ?, ?)",
            (key, inci[:500], risk_level, int(time.time()))
        )
        await db.commit()


async def create_key(name: str, email: str | None, credits: int = 1000) -> str:
    """Generate a new API key and store it."""
    key = "cire-" + secrets.token_urlsafe(24)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO api_keys (key, name, email, credits, created_at) VALUES (?, ?, ?, ?, ?)",
            (key, name, email, credits, int(time.time()))
        )
        await db.commit()
    return key
