#!/usr/bin/env python3
"""Enrich CIRE Pro seed data (idempotent).

- Adds high-signal evidence references (from docs/research_sources_v1.md)
- Adds ingredient synergy/conflict pair rules
- Adds goal-based recommendation rows

Safe to run multiple times.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "cire.db"

EVIDENCE_ROWS = [
    ("Guidelines of care for the management of acne vulgaris", "PubMed", 2024, "https://pubmed.ncbi.nlm.nih.gov/38300170/", "A"),
    ("The efficacy of adapalene-benzoyl peroxide combination increases with number of acne lesions", "PubMed", 2011, "https://pubmed.ncbi.nlm.nih.gov/21439678/", "A"),
    ("Adapalene-benzoyl peroxide, a fixed-dose combination for acne vulgaris: multicenter randomized trial", "PubMed", 2007, "https://pubmed.ncbi.nlm.nih.gov/17655969/", "A"),
    ("Fixed-dose clindamycin 1.2% + benzoyl peroxide 3.1% + adapalene 0.15% gel (phase 3)", "PubMed", 2022, "https://pubmed.ncbi.nlm.nih.gov/34674160/", "A"),
    ("Triple-combination clindamycin/adapalene/BPO gel for moderate-severe acne", "PubMed", 2024, "https://pubmed.ncbi.nlm.nih.gov/39630680/", "B"),
    ("Systematic review + network meta-analysis of acne treatments", "PubMed", 2022, "https://pubmed.ncbi.nlm.nih.gov/35789996/", "A"),
    ("Ferulic acid stabilizes vitamins C+E and doubles photoprotection", "PubMed", 2005, "https://pubmed.ncbi.nlm.nih.gov/16185284/", "A"),
    ("Topical antioxidant solution (C+E+ferulic) protects against UV-induced damage", "PubMed", 2008, "https://pubmed.ncbi.nlm.nih.gov/18603326/", "B"),
    ("Niacinamide-containing moisturizer improves skin barrier in rosacea subjects", "PubMed", 2005, "https://pubmed.ncbi.nlm.nih.gov/16209160/", "B"),
    ("Niacinamide reduces hyperpigmentation and melanosome transfer", "PubMed", 2002, "https://pubmed.ncbi.nlm.nih.gov/12100180/", "B"),
    ("2% niacinamide effect on facial sebum production", "PubMed", 2006, "https://pubmed.ncbi.nlm.nih.gov/16766489/", "B"),
    ("Triple combination fluocinolone/hydroquinone/tretinoin in melasma (RCT)", "PubMed", 2008, "https://pubmed.ncbi.nlm.nih.gov/18616780/", "A"),
    ("Interventions for melasma (Cochrane review)", "PubMed", 2010, "https://pubmed.ncbi.nlm.nih.gov/20614435/", "A"),
    ("S2k guideline: Rosacea", "PubMed", 2022, "https://pubmed.ncbi.nlm.nih.gov/35929658/", "A"),
    ("Management of Acne Vulgaris: A Review", "PubMed", 2021, "https://pubmed.ncbi.nlm.nih.gov/34812859/", "B"),
]

PAIR_ROWS = [
    # ingredient_a, ingredient_b, pair_type, severity, rationale, evidence_level, evidence_title
    ("Adapalene", "Benzoyl Peroxide", "synergy", 3, "Guideline-backed acne efficacy in combination", "A", "Guidelines of care for the management of acne vulgaris"),
    ("Adapalene", "Clindamycin", "synergy", 2, "Triple-combination acne regimens improve outcomes", "A", "Fixed-dose clindamycin 1.2% + benzoyl peroxide 3.1% + adapalene 0.15% gel (phase 3)"),
    ("Benzoyl Peroxide", "Clindamycin", "synergy", 2, "Common evidence-based inflammatory acne combination", "A", "Fixed-dose clindamycin 1.2% + benzoyl peroxide 3.1% + adapalene 0.15% gel (phase 3)"),
    ("Ascorbic Acid", "Tocopherol", "synergy", 2, "Antioxidant pairing improves photoprotection signal", "A", "Ferulic acid stabilizes vitamins C+E and doubles photoprotection"),
    ("Ascorbic Acid", "Ferulic Acid", "synergy", 2, "Ferulic acid can stabilize vitamin C formulations", "A", "Ferulic acid stabilizes vitamins C+E and doubles photoprotection"),
    ("Tocopherol", "Ferulic Acid", "synergy", 1, "Antioxidant stack support in topical solutions", "B", "Topical antioxidant solution (C+E+ferulic) protects against UV-induced damage"),
    ("Niacinamide", "Ceramide", "synergy", 2, "Barrier support combination with good tolerability", "B", "Niacinamide-containing moisturizer improves skin barrier in rosacea subjects"),
    ("Niacinamide", "Ascorbic Acid", "synergy", 1, "Adjunct brightening strategy in pigmentation care", "B", "Niacinamide reduces hyperpigmentation and melanosome transfer"),
    ("Retinol", "Glycolic Acid", "conflict", 2, "Retinoid + strong AHA stacking may raise irritation risk", "B", "Management of Acne Vulgaris: A Review"),
    ("Retinol", "Salicylic Acid", "conflict", 2, "Retinoid + BHA stacking may increase tolerability issues", "B", "Management of Acne Vulgaris: A Review"),
    ("Adapalene", "Salicylic Acid", "conflict", 2, "Concurrent keratolytics can worsen irritation in sensitive users", "B", "The efficacy of adapalene-benzoyl peroxide combination increases with number of acne lesions"),
    ("Hydroquinone", "Tretinoin", "synergy", 2, "Established depigmenting combination in melasma protocols", "A", "Triple combination fluocinolone/hydroquinone/tretinoin in melasma (RCT)"),
]

GOAL_ROWS = [
    # goal_tag, ingredient_name, role, priority, evidence_level, evidence_title
    ("acne", "Adapalene", "primary active", 100, "A", "Guidelines of care for the management of acne vulgaris"),
    ("acne", "Benzoyl Peroxide", "antimicrobial adjunct", 95, "A", "Guidelines of care for the management of acne vulgaris"),
    ("acne", "Clindamycin", "inflammatory lesion adjunct", 88, "A", "Fixed-dose clindamycin 1.2% + benzoyl peroxide 3.1% + adapalene 0.15% gel (phase 3)"),
    ("acne", "Niacinamide", "barrier/tolerance support", 80, "B", "Management of Acne Vulgaris: A Review"),
    ("brightening", "Ascorbic Acid", "antioxidant brightening", 95, "A", "Ferulic acid stabilizes vitamins C+E and doubles photoprotection"),
    ("brightening", "Niacinamide", "pigment transfer modulation", 90, "B", "Niacinamide reduces hyperpigmentation and melanosome transfer"),
    ("brightening", "Hydroquinone", "targeted depigmenting active", 85, "A", "Interventions for melasma (Cochrane review)"),
    ("antiaging", "Retinol", "cell turnover support", 95, "B", "Management of Acne Vulgaris: A Review"),
    ("antiaging", "Ascorbic Acid", "photodamage antioxidant support", 82, "A", "Topical antioxidant solution (C+E+ferulic) protects against UV-induced damage"),
    ("antiaging", "Tocopherol", "antioxidant support", 75, "B", "Topical antioxidant solution (C+E+ferulic) protects against UV-induced damage"),
    ("barrier", "Niacinamide", "barrier reinforcement", 96, "B", "Niacinamide-containing moisturizer improves skin barrier in rosacea subjects"),
    ("barrier", "Ceramide", "barrier lipid replenishment", 92, "B", "Niacinamide-containing moisturizer improves skin barrier in rosacea subjects"),
]


def get_ref_id(cur: sqlite3.Cursor, title: str):
    cur.execute("SELECT id FROM evidence_refs WHERE title = ?", (title,))
    row = cur.fetchone()
    return row[0] if row else None


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # evidence refs upsert by title
    for title, source, year, url, level in EVIDENCE_ROWS:
        cur.execute("SELECT id FROM evidence_refs WHERE title = ?", (title,))
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO evidence_refs (title, source, year, url, evidence_level) VALUES (?, ?, ?, ?, ?)",
            (title, source, year, url, level),
        )

    # ingredient pairs upsert by unique tuple
    for a, b, pair_type, severity, rationale, level, evidence_title in PAIR_ROWS:
        ref_id = get_ref_id(cur, evidence_title)
        cur.execute(
            "SELECT id FROM ingredient_pairs WHERE ingredient_a=? AND ingredient_b=? AND pair_type=?",
            (a, b, pair_type),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO ingredient_pairs
            (ingredient_a, ingredient_b, pair_type, severity, rationale, evidence_level, evidence_ref_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (a, b, pair_type, severity, rationale, level, ref_id),
        )

    # formulation goals upsert by goal+ingredient
    for goal, ingredient, role, priority, level, evidence_title in GOAL_ROWS:
        ref_id = get_ref_id(cur, evidence_title)
        cur.execute(
            "SELECT id FROM formulation_goals WHERE lower(goal_tag)=lower(?) AND ingredient_name=?",
            (goal, ingredient),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO formulation_goals
            (goal_tag, ingredient_name, role, priority, evidence_level, evidence_ref_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (goal, ingredient, role, priority, level, ref_id),
        )

    con.commit()

    cur.execute("SELECT COUNT(*) FROM evidence_refs")
    refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ingredient_pairs")
    pairs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM formulation_goals")
    goals = cur.fetchone()[0]

    print(f"Done. evidence_refs={refs}, ingredient_pairs={pairs}, formulation_goals={goals}")
    con.close()


if __name__ == "__main__":
    main()
