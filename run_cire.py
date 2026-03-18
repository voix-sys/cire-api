#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_cire.py — Minimal local runner for CIRE v0.1.1 compute_result (no external calls).

Usage:
  python run_cire.py --ingredients ingredient_dataset.json --interactions interaction_dataset.json --inci "Water, Retinol, Glycolic Acid"
  echo "Water, Parfum" | python run_cire.py --ingredients ingredient_dataset.json --interactions interaction_dataset.json
"""

import argparse
import json
import re
from typing import Any, Dict, List, Tuple, Set


EVIDENCE_STRENGTH = {
    "EU restriction list": 95,
    "FDA advisory": 90,
    "CIR report": 85,
    "Peer-reviewed consensus": 80,
    "Industry consensus": 65,
    "Controversial / weak evidence": 50,
}

CATEGORY_ORDER = [
    "irritation_risk",
    "allergen_risk",
    "pregnancy_risk",
    "acne_risk",
    "interaction_risk",
]

DEDUCTION_TABLE = {
    "irritation_risk": {1: -3, 2: -8, 3: -15},
    "allergen_risk": {1: -5, 2: -10, 3: -20},
    "pregnancy_risk": {1: -10, 2: -20, 3: -30},
    "acne_risk": {1: -3, 2: -6, 3: -10},
    "interaction_risk": {1: -5, 2: -8, 3: -10},
}

_WS_RE = re.compile(r"\s+")
_PARENS_RE = re.compile(r"\s*\([^)]*\)\s*")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(s: str) -> str:
    s2 = s.strip()
    s2 = s2.rstrip(".")
    s2 = _WS_RE.sub(" ", s2)
    return s2.lower()


def strip_parentheses(s: str) -> str:
    return _WS_RE.sub(" ", _PARENS_RE.sub(" ", s)).strip()


def tokenize_inci(inci: str) -> List[str]:
    parts = re.split(r"[,;/]", inci)
    out: List[str] = []
    for p in parts:
        t = _WS_RE.sub(" ", p.strip()).rstrip(".")
        if t:
            out.append(t)
    return out


def build_key_map(ingredient_dataset: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    key_map: Dict[str, List[Dict[str, Any]]] = {}
    for rec in ingredient_dataset:
        keys = [rec["ingredient_name"]] + list(rec.get("aliases", []))
        for k in keys:
            for variant in (k, strip_parentheses(k)):
                nk = normalize(variant)
                if not nk:
                    continue
                key_map.setdefault(nk, []).append(rec)
    return key_map


def compute_result(
    inci: str,
    ingredient_dataset: List[Dict[str, Any]],
    interaction_dataset: List[Dict[str, Any]],
) -> Dict[str, Any]:
    tokens = tokenize_inci(inci)
    key_map = build_key_map(ingredient_dataset)

    # Dedup by (ingredient_name, risk_category) regardless of duplicate token occurrences
    matched_records: Dict[Tuple[str, str], Dict[str, Any]] = {}
    present_ingredient_names: Set[str] = set()

    for tok in tokens:
        candidates: List[Dict[str, Any]] = []
        for variant in (tok, strip_parentheses(tok)):
            nk = normalize(variant)
            candidates.extend(key_map.get(nk, []))

        # Multi-record match: include ALL matched records across categories
        for rec in candidates:
            k = (rec["ingredient_name"], rec["risk_category"])
            matched_records[k] = rec
            present_ingredient_names.add(rec["ingredient_name"])

    matched_ingredients: List[Dict[str, Any]] = []
    for (iname, rcat), rec in matched_records.items():
        ev = rec["evidence_basis"]
        matched_ingredients.append(
            {
                "ingredient_name": iname,
                "risk_category": rcat,
                "severity": int(rec["severity"]),
                "evidence_basis": ev,
                "evidence_strength": int(EVIDENCE_STRENGTH[ev]),
            }
        )

    # Deterministic ordering: category order + ingredient_name asc
    matched_ingredients.sort(key=lambda x: (CATEGORY_ORDER.index(x["risk_category"]), x["ingredient_name"]))

    # Interactions: preserve dataset order; preserve pair order as stored
    matched_interactions: List[Dict[str, Any]] = []
    for rule in interaction_dataset:
        a, b = rule["pair"][0], rule["pair"][1]
        if a in present_ingredient_names and b in present_ingredient_names:
            ev = rule["evidence_basis"]
            matched_interactions.append(
                {
                    "pair": [a, b],
                    "risk_category": "interaction_risk",
                    "severity": int(rule["severity"]),
                    "reason": rule["reason"],  # do not rewrite
                    "evidence_basis": ev,
                    "evidence_strength": int(EVIDENCE_STRENGTH[ev]),
                }
            )

    # Category max severities (highest once per category)
    cat_max = {c: 0 for c in CATEGORY_ORDER}
    for m in matched_ingredients:
        c = m["risk_category"]
        cat_max[c] = max(cat_max[c], int(m["severity"]))
    cat_max["interaction_risk"] = max([0] + [int(m["severity"]) for m in matched_interactions])

    category_results: Dict[str, Dict[str, int]] = {}
    total = 100
    for c in CATEGORY_ORDER:
        sev = int(cat_max[c])
        ded = int(DEDUCTION_TABLE[c].get(sev, 0)) if sev > 0 else 0
        category_results[c] = {"max_severity": sev, "deduction": ded}
        total += ded

    risk_score = max(0, total)
    if risk_score >= 80:
        risk_level = "low"
    elif risk_score >= 50:
        risk_level = "moderate"
    else:
        risk_level = "high"

    strengths = [m["evidence_strength"] for m in matched_ingredients] + [m["evidence_strength"] for m in matched_interactions]
    confidence_score = min(strengths) if strengths else 100

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence_score": confidence_score,
        "category_results": category_results,
        "matches": {
            "ingredients": matched_ingredients,
            "interactions": matched_interactions,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run CIRE v0.1.1 locally (deterministic, no external calls).")
    ap.add_argument("--ingredients", default="ingredient_dataset.json")
    ap.add_argument("--interactions", default="interaction_dataset.json")
    ap.add_argument("--inci", default=None, help="INCI string. If omitted, reads from stdin.")
    args = ap.parse_args()

    ingredient_dataset = load_json(args.ingredients)
    interaction_dataset = load_json(args.interactions)

    if args.inci is None:
        inci = input().strip()
    else:
        inci = args.inci

    result = compute_result(inci, ingredient_dataset, interaction_dataset)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
