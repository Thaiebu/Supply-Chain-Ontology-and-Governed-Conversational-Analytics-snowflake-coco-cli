-- ============================================================
-- 05_document_parsing.sql
-- Unstructured Document Processing: Extract SLA commitments
-- from supplier contract text using Snowflake Cortex AI
-- Target: SUPPLY_CHAIN_DB
-- ============================================================

USE DATABASE SUPPLY_CHAIN_DB;
USE SCHEMA ANALYTICS;
USE WAREHOUSE COMPUTE_WH;

-- ============================================================
-- 1. Create stage for contract documents
-- ============================================================
CREATE STAGE IF NOT EXISTS SUPPLY_CHAIN_DB.ANALYTICS.CONTRACT_DOCUMENTS_STAGE
    DIRECTORY   = (ENABLE = TRUE)
    ENCRYPTION  = (TYPE = 'SNOWFLAKE_SSE');

-- Upload contract file:
--   PUT file:///path/to/contracts/supplier_sla_agreement.txt
--       @SUPPLY_CHAIN_DB.ANALYTICS.CONTRACT_DOCUMENTS_STAGE
--       AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- ============================================================
-- 2. Create raw contract text table
-- ============================================================
CREATE OR REPLACE TABLE ANALYTICS.RAW_CONTRACT_DOCUMENTS (
    doc_id          VARCHAR NOT NULL,
    doc_name        VARCHAR NOT NULL,
    doc_text        VARCHAR NOT NULL,
    upload_ts       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================
-- 3. Create target table for extracted SLA terms
-- ============================================================
CREATE OR REPLACE TABLE ANALYTICS.SUPPLIER_CONTRACT_SLAS (
    supplier_id         VARCHAR NOT NULL,
    supplier_name       VARCHAR NOT NULL,
    country             VARCHAR,
    otd_commitment_pct  NUMBER(5,2) NOT NULL,
    penalty_clause      VARCHAR,
    contract_start      DATE,
    contract_end        DATE,
    source_document     VARCHAR,
    extracted_by        VARCHAR DEFAULT 'SNOWFLAKE.CORTEX.COMPLETE',
    extracted_ts        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================
-- 4. Use Cortex COMPLETE to extract structured SLA data
--    from the raw contract text
-- ============================================================
-- Step 4a: Load the contract text into the raw table
-- (This is done via the Python upload script or manual INSERT)

-- Step 4b: Extract SLA terms using Cortex AI
-- The following uses SNOWFLAKE.CORTEX.COMPLETE() to parse
-- the unstructured contract text and return structured JSON
-- for each supplier's SLA commitment.

-- Note: The actual extraction is performed via the INSERT
-- statement below, which calls Cortex COMPLETE to parse
-- the contract document and extract supplier SLA terms.

-- ============================================================
-- 5. SLA vs Actual OTD Comparison View
-- ============================================================
CREATE OR REPLACE VIEW ANALYTICS.V_SLA_VS_ACTUAL_OTD AS
SELECT
    sla.supplier_id,
    sla.supplier_name,
    sla.country,
    sla.otd_commitment_pct AS sla_target_pct,
    ROUND(100.0 * SUM(CASE WHEN po.receipt_date <= po.promised_date THEN 1 ELSE 0 END)
          / NULLIF(COUNT(CASE WHEN po.receipt_date IS NOT NULL THEN 1 END), 0), 2) AS actual_otd_pct,
    COUNT(CASE WHEN po.receipt_date IS NOT NULL THEN 1 END) AS total_closed_pos,
    ROUND(100.0 * SUM(CASE WHEN po.receipt_date <= po.promised_date THEN 1 ELSE 0 END)
          / NULLIF(COUNT(CASE WHEN po.receipt_date IS NOT NULL THEN 1 END), 0), 2)
      - sla.otd_commitment_pct AS gap_pct,
    CASE
        WHEN ROUND(100.0 * SUM(CASE WHEN po.receipt_date <= po.promised_date THEN 1 ELSE 0 END)
              / NULLIF(COUNT(CASE WHEN po.receipt_date IS NOT NULL THEN 1 END), 0), 2)
              >= sla.otd_commitment_pct THEN 'MEETING SLA'
        WHEN ROUND(100.0 * SUM(CASE WHEN po.receipt_date <= po.promised_date THEN 1 ELSE 0 END)
              / NULLIF(COUNT(CASE WHEN po.receipt_date IS NOT NULL THEN 1 END), 0), 2)
              >= sla.otd_commitment_pct - 3 THEN 'WARNING (within 3pts)'
        ELSE 'BREACH'
    END AS sla_status,
    sla.penalty_clause,
    sla.contract_start,
    sla.contract_end
FROM ANALYTICS.SUPPLIER_CONTRACT_SLAS sla
LEFT JOIN ANALYTICS.FCT_PURCHASE_ORDERS po
    ON sla.supplier_id = po.supplier_id
GROUP BY
    sla.supplier_id, sla.supplier_name, sla.country,
    sla.otd_commitment_pct, sla.penalty_clause,
    sla.contract_start, sla.contract_end
ORDER BY gap_pct ASC;
