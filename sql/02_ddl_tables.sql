-- ============================================================
-- 02_ddl_tables.sql
-- Supply Chain Base Tables: Dimensions first, then Facts
-- Target: SUPPLY_CHAIN_DB.ANALYTICS
-- ============================================================

USE DATABASE SUPPLY_CHAIN_DB;
USE SCHEMA ANALYTICS;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE OR REPLACE TABLE DIM_SUPPLIER (
    supplier_id   VARCHAR    NOT NULL PRIMARY KEY,
    supplier_name VARCHAR    NOT NULL,
    country       VARCHAR    NOT NULL,
    lead_time_days INTEGER   NOT NULL,
    rating        NUMBER(2,1)
);

CREATE OR REPLACE TABLE DIM_PLANT (
    plant_id       VARCHAR   NOT NULL PRIMARY KEY,
    plant_name     VARCHAR   NOT NULL,
    city           VARCHAR   NOT NULL,
    country        VARCHAR   NOT NULL,
    capacity_units INTEGER   NOT NULL
);

CREATE OR REPLACE TABLE DIM_CUSTOMER (
    customer_id    VARCHAR   NOT NULL PRIMARY KEY,
    customer_name  VARCHAR   NOT NULL,
    industry       VARCHAR   NOT NULL,
    country        VARCHAR   NOT NULL,
    tier           VARCHAR   NOT NULL
);

CREATE OR REPLACE TABLE DIM_PART (
    part_id      VARCHAR     NOT NULL PRIMARY KEY,
    part_name    VARCHAR     NOT NULL,
    category     VARCHAR     NOT NULL,
    unit_cost    NUMBER(12,2) NOT NULL,
    supplier_id  VARCHAR     NOT NULL REFERENCES DIM_SUPPLIER(supplier_id),
    plant_id     VARCHAR     NOT NULL REFERENCES DIM_PLANT(plant_id)
);

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE OR REPLACE TABLE FCT_PURCHASE_ORDERS (
    po_id               VARCHAR       NOT NULL PRIMARY KEY,
    part_id             VARCHAR       NOT NULL REFERENCES DIM_PART(part_id),
    supplier_id         VARCHAR       NOT NULL REFERENCES DIM_SUPPLIER(supplier_id),
    plant_id            VARCHAR       NOT NULL REFERENCES DIM_PLANT(plant_id),
    order_qty           INTEGER       NOT NULL,
    received_qty        INTEGER,
    unit_cost_ea        NUMBER(12,2)  NOT NULL,
    freight_cost        NUMBER(12,2)  DEFAULT 0,
    customs_tariff_cost NUMBER(12,2)  DEFAULT 0,
    promised_date       DATE          NOT NULL,
    receipt_date        DATE,
    po_status           VARCHAR       NOT NULL
);

CREATE OR REPLACE TABLE FCT_SHIPMENTS (
    ship_id                VARCHAR   NOT NULL PRIMARY KEY,
    po_id                  VARCHAR   NOT NULL REFERENCES FCT_PURCHASE_ORDERS(po_id),
    carrier_name           VARCHAR   NOT NULL,
    origin_plant_id        VARCHAR   NOT NULL REFERENCES DIM_PLANT(plant_id),
    dest_plant_id          VARCHAR   NOT NULL REFERENCES DIM_PLANT(plant_id),
    ship_date              DATE      NOT NULL,
    estimated_delivery_date DATE     NOT NULL,
    actual_delivery_date   DATE,
    transit_status         VARCHAR   NOT NULL
);

CREATE OR REPLACE TABLE FCT_CUSTOMER_ORDERS (
    order_id        VARCHAR   NOT NULL PRIMARY KEY,
    customer_id     VARCHAR   NOT NULL REFERENCES DIM_CUSTOMER(customer_id),
    part_id         VARCHAR   NOT NULL REFERENCES DIM_PART(part_id),
    plant_id        VARCHAR   NOT NULL REFERENCES DIM_PLANT(plant_id),
    ordered_qty     INTEGER   NOT NULL,
    shipped_qty     INTEGER,
    request_date    DATE      NOT NULL,
    shipped_date    DATE,
    delivery_status VARCHAR   NOT NULL
);
