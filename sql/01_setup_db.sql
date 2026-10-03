-- ============================================================
-- 01_setup_db.sql
-- Database, Schema, Warehouse, and Stage Setup
-- Run this FIRST before any other scripts
-- ============================================================

-- ============================================================
-- DATABASE
-- ============================================================

CREATE DATABASE IF NOT EXISTS SUPPLY_CHAIN_DB;

-- ============================================================
-- SCHEMAS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS SUPPLY_CHAIN_DB.ANALYTICS;
CREATE SCHEMA IF NOT EXISTS SUPPLY_CHAIN_DB.STAGING;

-- ============================================================
-- WAREHOUSE
-- ============================================================

CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE;

-- ============================================================
-- SET ACTIVE CONTEXT
-- ============================================================

USE DATABASE SUPPLY_CHAIN_DB;
USE SCHEMA ANALYTICS;
USE WAREHOUSE COMPUTE_WH;

-- ============================================================
-- INTERNAL STAGE FOR SEMANTIC MODEL YAML
-- ============================================================

CREATE STAGE IF NOT EXISTS SUPPLY_CHAIN_DB.ANALYTICS.SEMANTIC_MODELS_STAGE
    DIRECTORY   = (ENABLE = TRUE)
    ENCRYPTION  = (TYPE = 'SNOWFLAKE_SSE');
