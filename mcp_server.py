#!/usr/bin/env python3
"""
CIRE MCP Server — Cosmetic Ingredient Risk Engine
Exposes CIRE as an MCP tool for Claude, Cursor, Windsurf, and other AI agents.

Usage:
  python mcp_server.py

Connect via MCP client:
  stdio transport (for Claude Desktop, Cursor, etc.)
"""

import sys
import json
import asyncio
from pathlib import Path

# CIRE core
CIRE_DIR = Path(__file__).parent
sys.path.insert(0, str(CIRE_DIR))
from run_cire import compute_result, load_json

# Load datasets once
INGREDIENT_DATASET = load_json(str(CIRE_DIR / "ingredient_dataset.json"))
INTERACTION_DATASET = load_json(str(CIRE_DIR / "interaction_dataset.json"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("cire")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="analyze_ingredients",
            description=(
                "Analyze a cosmetic product's INCI ingredient list for safety risks. "
                "Returns a deterministic JSON risk score across 5 categories: "
                "irritation, allergen, pregnancy, acne, and ingredient interactions. "
                "Designed for shopping agents, catalog filters, compliance pipelines, "
                "and K-beauty recommendation engines."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "inci": {
                        "type": "string",
                        "description": (
                            "Comma-separated INCI ingredient list. "
                            "Example: 'Water, Retinol, Glycolic Acid, Phenoxyethanol'"
                        )
                    }
                },
                "required": ["inci"]
            }
        ),
        types.Tool(
            name="check_pregnancy_safety",
            description=(
                "Quick check: is this product safe during pregnancy? "
                "Returns a simple safe/caution/avoid verdict with reasons."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "inci": {
                        "type": "string",
                        "description": "Comma-separated INCI ingredient list."
                    }
                },
                "required": ["inci"]
            }
        ),
        types.Tool(
            name="check_allergen_risk",
            description=(
                "Check if a product contains known EU fragrance allergens or "
                "common contact allergens. Returns matched allergens with severity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "inci": {
                        "type": "string",
                        "description": "Comma-separated INCI ingredient list."
                    }
                },
                "required": ["inci"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    inci = arguments.get("inci", "").strip()
    if not inci:
        return [types.TextContent(type="text", text='{"error": "inci is required"}')]

    result = compute_result(inci, INGREDIENT_DATASET, INTERACTION_DATASET)

    if name == "analyze_ingredients":
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "check_pregnancy_safety":
        preg = result["category_results"]["pregnancy_risk"]
        matches = [m for m in result["matches"]["ingredients"] if m["risk_category"] == "pregnancy_risk"]
        sev = preg["max_severity"]
        verdict = "safe" if sev == 0 else "caution" if sev == 1 else "avoid" if sev >= 2 else "safe"
        out = {
            "verdict": verdict,
            "severity": sev,
            "flagged_ingredients": [{"name": m["ingredient_name"], "severity": m["severity"], "evidence": m["evidence_basis"]} for m in matches]
        }
        return [types.TextContent(type="text", text=json.dumps(out, ensure_ascii=False))]

    elif name == "check_allergen_risk":
        allergens = [m for m in result["matches"]["ingredients"] if m["risk_category"] == "allergen_risk"]
        out = {
            "allergen_count": len(allergens),
            "max_severity": result["category_results"]["allergen_risk"]["max_severity"],
            "allergens": [{"name": m["ingredient_name"], "severity": m["severity"], "evidence": m["evidence_basis"]} for m in allergens]
        }
        return [types.TextContent(type="text", text=json.dumps(out, ensure_ascii=False))]

    return [types.TextContent(type="text", text='{"error": "unknown tool"}')]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
