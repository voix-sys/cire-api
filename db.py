"""
db.py — SQLite persistence for CIRE API keys, usage logs, and Pro feature metadata.
"""

import aiosqlite
import os
import secrets
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent))) / "cire.db"
RESEARCH_MD_PATH = Path(__file__).parent / "docs" / "research_sources_v1.md"


async def _ensure_api_keys_tier_column(db: aiosqlite.Connection) -> None:
    async with db.execute("PRAGMA table_info(api_keys)") as cur:
        cols = await cur.fetchall()
    col_names = {c[1] for c in cols}
    if "tier" not in col_names:
        await db.execute("ALTER TABLE api_keys ADD COLUMN tier TEXT NOT NULL DEFAULT 'free'")


async def _seed_evidence_refs(db: aiosqlite.Connection) -> None:
    async with db.execute("SELECT COUNT(*) FROM evidence_refs") as cur:
        count = (await cur.fetchone())[0]
    if count > 0:
        return

    # Minimal deterministic seed rows sourced from docs/research_sources_v1.md
    starter_rows = [
        (
            "Guidelines of care for the management of acne vulgaris",
            "PubMed",
            2024,
            "https://pubmed.ncbi.nlm.nih.gov/38300170/",
            "A",
        ),
        (
            "Adapalene-benzoyl peroxide fixed-dose combination trial",
            "PubMed",
            2007,
            "https://pubmed.ncbi.nlm.nih.gov/17655969/",
            "A",
        ),
        (
            "Ferulic acid stabilizes vitamins C+E and doubles photoprotection",
            "PubMed",
            2005,
            "https://pubmed.ncbi.nlm.nih.gov/16185284/",
            "A",
        ),
        (
            "Management of Acne Vulgaris: A Review",
            "PubMed",
            2021,
            "https://pubmed.ncbi.nlm.nih.gov/34812859/",
            "B",
        ),
        (
            "Alpha + beta hydroxy acid peels in post-acne pigmentation",
            "PubMed",
            2022,
            "https://pubmed.ncbi.nlm.nih.gov/35309278/",
            "B",
        ),
    ]

    await db.executemany(
        """
        INSERT INTO evidence_refs (title, source, year, url, evidence_level)
        VALUES (?, ?, ?, ?, ?)
        """,
        starter_rows,
    )


async def _seed_ingredient_pairs(db: aiosqlite.Connection) -> None:
    async with db.execute("SELECT COUNT(*) FROM ingredient_pairs") as cur:
        count = (await cur.fetchone())[0]
    if count > 0:
        return

    rows = [
        (
            "Adapalene",
            "Benzoyl Peroxide",
            "synergy",
            3,
            "Strong guideline/RCT support for acne efficacy in combination",
            "A",
            2,
        ),
        (
            "Ascorbic Acid",
            "Tocopherol",
            "synergy",
            2,
            "Antioxidant pairing improves photoprotection signal",
            "A",
            3,
        ),
        (
            "Ascorbic Acid",
            "Ferulic Acid",
            "synergy",
            2,
            "Ferulic acid can stabilize vitamin C formulations",
            "A",
            3,
        ),
        (
            "Retinol",
            "Glycolic Acid",
            "conflict",
            2,
            "Retinoid + strong AHA stacking may raise irritation risk",
            "B",
            4,
        ),
        (
            "Retinol",
            "Salicylic Acid",
            "conflict",
            2,
            "Retinoid + BHA stacking may increase tolerability issues",
            "B",
            5,
        ),
    ]

    await db.executemany(
        """
        INSERT INTO ingredient_pairs (
            ingredient_a, ingredient_b, pair_type, severity, rationale, evidence_level, evidence_ref_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


async def _seed_formulation_goals(db: aiosqlite.Connection) -> None:
    async with db.execute("SELECT COUNT(*) FROM formulation_goals") as cur:
        count = (await cur.fetchone())[0]
    if count > 0:
        return

    rows = [
        ("acne", "Adapalene", "primary active", 100, "A", 1),
        ("acne", "Benzoyl Peroxide", "antimicrobial adjunct", 95, "A", 2),
        ("acne", "Niacinamide", "barrier/tolerance support", 80, "B", 4),
        ("brightening", "Ascorbic Acid", "antioxidant brightening", 95, "A", 3),
        ("brightening", "Niacinamide", "pigment transfer modulation", 85, "B", 4),
        ("antiaging", "Retinol", "cell turnover support", 90, "B", 4),
        ("antiaging", "Ascorbic Acid", "photodamage antioxidant support", 80, "A", 3),
        ("barrier", "Niacinamide", "barrier reinforcement", 95, "B", 4),
        ("barrier", "Ceramide", "barrier lipid replenishment", 90, "B", 4),
    ]

    await db.executemany(
        """
        INSERT INTO formulation_goals (
            goal_tag, ingredient_name, role, priority, evidence_level, evidence_ref_id
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                key         TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT,
                credits     INTEGER NOT NULL DEFAULT 0,
                tier        TEXT NOT NULL DEFAULT 'free',
                created_at  INTEGER NOT NULL
            )
            """
        )
        await _ensure_api_keys_tier_column(db)

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key     TEXT NOT NULL,
                inci        TEXT NOT NULL,
                risk_level  TEXT,
                called_at   INTEGER NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_refs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                source          TEXT,
                year            INTEGER,
                url             TEXT,
                evidence_level  TEXT NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ingredient_pairs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_a     TEXT NOT NULL,
                ingredient_b     TEXT NOT NULL,
                pair_type        TEXT NOT NULL, -- synergy | conflict
                severity         INTEGER NOT NULL,
                rationale        TEXT,
                evidence_level   TEXT NOT NULL,
                evidence_ref_id  INTEGER,
                FOREIGN KEY (evidence_ref_id) REFERENCES evidence_refs(id)
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS formulation_goals (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_tag         TEXT NOT NULL,
                ingredient_name  TEXT NOT NULL,
                role             TEXT,
                priority         INTEGER NOT NULL DEFAULT 50,
                evidence_level   TEXT NOT NULL,
                evidence_ref_id  INTEGER,
                FOREIGN KEY (evidence_ref_id) REFERENCES evidence_refs(id)
            )
            """
        )

        await _seed_evidence_refs(db)
        await _seed_ingredient_pairs(db)
        await _seed_formulation_goals(db)

        # Seed a dev key if table is empty
        async with db.execute("SELECT COUNT(*) FROM api_keys") as cur:
            count = (await cur.fetchone())[0]
        if count == 0:
            seed_key = os.environ.get("SEED_API_KEY", "")
            if seed_key:
                await db.execute(
                    "INSERT INTO api_keys (key, name, email, credits, tier, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (seed_key, "dev", None, 9999, "pro", int(time.time())),
                )
        await db.commit()


async def get_key_info(key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT key, name, email, credits, tier FROM api_keys WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_ingredient_pairs() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM ingredient_pairs") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_formulation_goal_rows(goal_tag: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM formulation_goals WHERE lower(goal_tag) = lower(?) ORDER BY priority DESC, ingredient_name ASC",
            (goal_tag,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_evidence_refs_by_ids(ref_ids: list[int]) -> list[dict]:
    if not ref_ids:
        return []
    placeholders = ",".join(["?"] * len(ref_ids))
    query = f"SELECT * FROM evidence_refs WHERE id IN ({placeholders}) ORDER BY id ASC"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(ref_ids)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def deduct_credit(key: str) -> int:
    """Deduct 1 credit. Returns remaining credits."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET credits = credits - 1 WHERE key = ?", (key,))
        await db.commit()
        async with db.execute("SELECT credits FROM api_keys WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def log_usage(key: str, inci: str, risk_level: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_log (api_key, inci, risk_level, called_at) VALUES (?, ?, ?, ?)",
            (key, inci[:500], risk_level, int(time.time())),
        )
        await db.commit()


async def add_credits(key: str, credits: int) -> int:
    """Add credits to an existing key. Returns new total."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET credits = credits + ? WHERE key = ?", (credits, key))
        await db.commit()
        async with db.execute("SELECT credits FROM api_keys WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def set_key_tier(key: str, tier: str) -> str | None:
    """Set API key tier (e.g., free/pro). Returns updated tier or None if key not found."""
    normalized = (tier or "free").strip().lower()
    if normalized not in {"free", "pro", "enterprise"}:
        normalized = "free"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET tier = ? WHERE key = ?", (normalized, key))
        await db.commit()
        async with db.execute("SELECT tier FROM api_keys WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def create_key(name: str, email: str | None, credits: int = 1000, tier: str = "free") -> str:
    """Generate a new API key and store it."""
    key = "cire-" + secrets.token_urlsafe(24)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO api_keys (key, name, email, credits, tier, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (key, name, email, credits, tier, int(time.time())),
        )
        await db.commit()
    return key
