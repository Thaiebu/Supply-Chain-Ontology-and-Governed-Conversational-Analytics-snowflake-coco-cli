-- ============================================================
-- 04_dynamic_table_pipeline.sql
-- Staging table + Dynamic Table pipeline proof
-- Target: SUPPLY_CHAIN_DB
-- ============================================================

USE DATABASE SUPPLY_CHAIN_DB;

-- ============================================================
-- Staging table for messy ERP events
-- ============================================================
CREATE OR REPLACE TABLE STAGING.RAW_DELIVERY_EVENTS (
  event_id VARCHAR,
  po_id VARCHAR,
  event_timestamp TIMESTAMP_NTZ,
  raw_status_code VARCHAR,
  source_system VARCHAR
);

-- ============================================================
-- Dynamic Table that cleans & normalizes statuses
-- ============================================================
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_DELIVERY_SUMMARY
  TARGET_LAG = 'DOWNSTREAM'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
  po_id,
  MAX(event_timestamp) AS last_updated,
  CASE
    WHEN UPPER(raw_status_code) IN ('DLV', 'COMPL', 'RECEIVED') THEN 'DELIVERED'
    WHEN UPPER(raw_status_code) IN ('DELAY', 'HOLD', 'LATE') THEN 'DELAYED'
    ELSE 'IN_TRANSIT'
  END AS normalized_status
FROM STAGING.RAW_DELIVERY_EVENTS
GROUP BY po_id, raw_status_code;
