---
name: supply-chain-ontology-validator
description: >
  Validates Snowflake supply chain semantic models and ontologies against
  physical schema foreign keys, canonical metric completeness, persona-level
  verified query coverage, and type-safety guardrails.
usage: >
  Invoke this skill before deploying or updating a semantic model YAML to a
  Snowflake stage. Run the companion script from the project root:
    python .cortex/skills/supply-chain-ontology-validator/validate_model.py \
      --model semantic_model/supply_chain_ontology.yaml
  The script exits 0 on full compliance and 1 on any failure.
---

# Supply Chain Ontology & Semantic Model Validator

## Purpose
This reusable CoCo skill automates validation of enterprise semantic models (YAML/DDL) against underlying Snowflake databases. It ensures that conversational AI agents (like Cortex Analyst) have complete, mathematically sound, and referentially verified ontologies before deploying to business users.

## When to Use
- Before deploying or updating semantic models to Snowflake stages.
- When adding new supply chain entities, dimensions, or metrics.
- During CI/CD pipelines to guarantee verified query accuracy and prevent LLM hallucination.

## Validation Checks
The skill performs four automated validation stages:

1. **Schema & Referential Integrity Check:**
   - Verifies that all tables defined in `tables:` exist in the model.
   - Verifies that all `relationships:` reference valid tables and that join columns are declared as dimensions with matching `data_type`.

2. **Canonical Metric Completeness Check:**
   - Confirms the presence of the 4 mandatory supply chain KPIs:
     - **On-Time Delivery (OTD):** Inbound Supplier, Carrier Transit, and Enterprise Canonical.
     - **Fill Rate:** Order quantity vs. fulfilled quantity ratio.
     - **Days of Inventory (DOI):** Stock vs. consumption rate.
     - **Landed Cost:** Base unit cost + freight allocation + tariffs/customs.

3. **Persona Query Coverage Check:**
   - Validates that verified queries exist for distinct business lenses:
     - *Procurement:* Supplier OTD, supplier rating, landed cost.
     - *Logistics:* Carrier SLA, transit delays, plant-to-plant routes.
     - *Planning:* Customer OTIF, inventory levels, order backlog.
     - *Executive:* Canonical enterprise metrics and blended ratios.

4. **Hallucination & Type Safety Guardrails:**
   - Ensures measures include `NULLIF` guards against division-by-zero.
   - Ensures counts and sums are cast to `DOUBLE` / `FLOAT` to prevent integer division truncation.

## Usage

```bash
python .cortex/skills/supply-chain-ontology-validator/validate_model.py \
  --model semantic_model/supply_chain_ontology.yaml
```

## Example Output
```
[INFO] Loading semantic model: semantic_model/supply_chain_ontology.yaml
=== 1. REFERENTIAL INTEGRITY ===
[PASS] All 7 tables declared in model
[PASS] 11/11 relationships reference valid tables with matching join columns

=== 2. CANONICAL KPI COMPLETENESS ===
[PASS] OTD metrics found (supplier_otd, carrier_otd, customer_otif, enterprise_otd)
[PASS] Fill Rate metric found
[PASS] Days of Inventory metric found
[PASS] Landed Cost metric found

=== 3. PERSONA QUERY COVERAGE ===
[PASS] Procurement: 4 verified queries
[PASS] Logistics: 3 verified queries
[PASS] Planning: 3 verified queries
[PASS] Executive: 4 verified queries

=== 4. TYPE SAFETY GUARDRAILS ===
[PASS] All ratio measures use NULLIF division guards

RESULT: PASS — Model is compliant and ready for deployment.
```
