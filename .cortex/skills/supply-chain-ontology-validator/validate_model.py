#!/usr/bin/env python3
"""
validate_model.py
Companion script for the 'supply-chain-ontology-validator' CoCo skill.
Validates a supply chain semantic model YAML for referential integrity,
canonical KPI completeness, persona query coverage, and type safety.
Exit 0 = PASS, Exit 1 = FAIL.
"""

import argparse
import os
import re
import sys

import yaml

# ── Required canonical KPI patterns (case-insensitive substring in measure names or exprs)
CANONICAL_KPIS = {
    "OTD": ["otd", "otif", "on_time", "on-time"],
    "Fill Rate": ["fill_rate", "fill rate"],
    "Days of Inventory": ["days_of_inventory", "doi", "days of inventory"],
    "Landed Cost": ["landed_cost", "landed cost"],
}

# ── Persona keyword mapping for verified query coverage
PERSONA_KEYWORDS = {
    "Procurement": ["supplier", "procurement", "vendor", "landed_cost", "landed cost", "purchase_order"],
    "Logistics": ["carrier", "shipment", "transit", "logistics", "freight", "delivery"],
    "Planning": ["customer", "otif", "planning", "inventory", "backlog", "demand"],
    "Executive": ["enterprise", "executive", "canonical", "blended", "overall", "weighted"],
}

EXPECTED_TABLES = [
    "suppliers", "plants", "customers", "parts",
    "purchase_orders", "shipments", "customer_orders",
]


def load_model(path: str) -> dict:
    if not os.path.exists(path):
        print(f"[FAIL] File not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def check_referential_integrity(model: dict) -> list[str]:
    """Verify relationships reference valid tables and join columns exist as dimensions."""
    errors = []
    tables = {t["name"]: t for t in model.get("tables", [])}
    table_names = set(tables.keys())

    # Check expected tables
    missing = [t for t in EXPECTED_TABLES if t not in table_names]
    if missing:
        errors.append(f"Missing required tables: {missing}")
    else:
        print(f"[PASS] All {len(EXPECTED_TABLES)} required tables declared in model")

    # Check relationships
    relationships = model.get("relationships", [])
    if not relationships:
        errors.append("No relationships defined in model")
        return errors

    valid_rels = 0
    for rel in relationships:
        left = rel.get("left_table", "")
        right = rel.get("right_table", "")
        left_cols = rel.get("left_columns", [])
        right_cols = rel.get("right_columns", [])

        if left not in table_names:
            errors.append(f"Relationship references unknown left_table: {left}")
            continue
        if right not in table_names:
            errors.append(f"Relationship references unknown right_table: {right}")
            continue

        # Verify join columns exist as dimensions in their respective tables
        left_dims = {d["name"] for d in tables[left].get("dimensions", [])}
        right_dims = {d["name"] for d in tables[right].get("dimensions", [])}

        for col in left_cols:
            if col not in left_dims:
                errors.append(f"Join column '{col}' not declared as dimension in table '{left}'")
        for col in right_cols:
            if col not in right_dims:
                errors.append(f"Join column '{col}' not declared as dimension in table '{right}'")

        valid_rels += 1

    if not errors or all("Missing required tables" in e for e in errors):
        print(f"[PASS] {valid_rels}/{len(relationships)} relationships reference valid tables with matching join columns")

    return errors


def check_canonical_kpis(model: dict) -> list[str]:
    """Verify all 4 canonical KPIs are present as measures/metrics."""
    errors = []

    # Collect all metric/measure names and expressions from tables and top-level
    all_text = ""
    for table in model.get("tables", []):
        for m in table.get("measures", []) + table.get("metrics", []):
            all_text += " " + m.get("name", "").lower()
            all_text += " " + m.get("expr", "").lower()
            all_text += " " + m.get("description", "").lower()
    # Top-level metrics
    for m in model.get("metrics", []):
        all_text += " " + m.get("name", "").lower()
        all_text += " " + m.get("expr", "").lower()
        all_text += " " + m.get("description", "").lower()

    for kpi_name, patterns in CANONICAL_KPIS.items():
        found = any(p in all_text for p in patterns)
        if found:
            print(f"[PASS] {kpi_name} metric found")
        else:
            errors.append(f"Canonical KPI missing: {kpi_name} (looked for: {patterns})")

    return errors


def check_persona_coverage(model: dict) -> list[str]:
    """Verify verified queries cover all 4 personas."""
    errors = []
    verified_queries = model.get("verified_queries", [])

    if not verified_queries:
        errors.append("No verified_queries defined in model")
        return errors

    for persona, keywords in PERSONA_KEYWORDS.items():
        matched = []
        for vq in verified_queries:
            vq_text = (
                vq.get("name", "") + " " +
                vq.get("question", "") + " " +
                vq.get("sql", "")
            ).lower()
            if any(kw in vq_text for kw in keywords):
                matched.append(vq.get("name", "unknown"))
        if matched:
            print(f"[PASS] {persona}: {len(matched)} verified queries")
        else:
            errors.append(f"No verified queries found for persona: {persona}")

    return errors


def check_type_safety(model: dict) -> list[str]:
    """Check that ratio/percentage measures use NULLIF guards."""
    errors = []
    ratio_measures_without_guard = []

    for table in model.get("tables", []):
        for measure in table.get("measures", []) + table.get("metrics", []):
            expr = measure.get("expr", "").lower()
            name = measure.get("name", "")
            if "/" in expr and "nullif" not in expr:
                ratio_measures_without_guard.append(f"{table['name']}.{name}")
    for measure in model.get("metrics", []):
        expr = measure.get("expr", "").lower()
        name = measure.get("name", "")
        if "/" in expr and "nullif" not in expr:
            ratio_measures_without_guard.append(f"(top-level).{name}")

    if ratio_measures_without_guard:
        errors.append(
            f"Measures with division but no NULLIF guard: {ratio_measures_without_guard}"
        )
    else:
        print("[PASS] All ratio measures use NULLIF division guards")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate a supply chain semantic model YAML."
    )
    parser.add_argument(
        "--model",
        default="semantic_model/supply_chain_ontology.yaml",
        help="Path to the semantic model YAML file.",
    )
    parser.add_argument("--database", default=None, help="Target Snowflake database (informational).")
    parser.add_argument("--schema", default=None, help="Target Snowflake schema (informational).")
    args = parser.parse_args()

    print(f"[INFO] Loading semantic model: {args.model}")
    if args.database:
        print(f"[INFO] Target: {args.database}.{args.schema or 'N/A'}")

    model = load_model(args.model)
    all_errors = []

    print("\n=== 1. REFERENTIAL INTEGRITY ===")
    all_errors.extend(check_referential_integrity(model))

    print("\n=== 2. CANONICAL KPI COMPLETENESS ===")
    all_errors.extend(check_canonical_kpis(model))

    print("\n=== 3. PERSONA QUERY COVERAGE ===")
    all_errors.extend(check_persona_coverage(model))

    print("\n=== 4. TYPE SAFETY GUARDRAILS ===")
    all_errors.extend(check_type_safety(model))

    print()
    if all_errors:
        print("=" * 55)
        print(f"RESULT: FAIL — {len(all_errors)} issue(s) detected:")
        for i, err in enumerate(all_errors, 1):
            print(f"  {i}. {err}")
        print("=" * 55)
        sys.exit(1)
    else:
        print("=" * 55)
        print("RESULT: PASS — Model is compliant and ready for deployment.")
        print("=" * 55)
        sys.exit(0)


if __name__ == "__main__":
    main()
