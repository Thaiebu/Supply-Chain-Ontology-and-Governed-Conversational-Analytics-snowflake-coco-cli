-- ============================================================
-- 03_seed_data.sql
-- Synthetic seed data with referential consistency
-- Target: SUPPLY_CHAIN_DB.ANALYTICS
-- ============================================================

USE DATABASE SUPPLY_CHAIN_DB;
USE SCHEMA ANALYTICS;

-- ============================================================
-- 1. DIM_SUPPLIER  (20 rows: India, UAE, Germany, USA, China)
-- ============================================================
INSERT INTO DIM_SUPPLIER VALUES
('SUP-001','Tata Steel Supply','India',14,4.5),
('SUP-002','Reliance Components','India',12,4.2),
('SUP-003','Mahindra Parts Co','India',10,3.8),
('SUP-004','Bharat Electronics','India',15,4.0),
('SUP-005','Emirates Metal Works','UAE',7,4.6),
('SUP-006','Dubai Precision Parts','UAE',6,4.3),
('SUP-007','Gulf Logistics Supply','UAE',8,3.9),
('SUP-008','Abu Dhabi Materials','UAE',9,4.1),
('SUP-009','Siemens Industrial','Germany',18,4.8),
('SUP-010','Bosch Components','Germany',16,4.7),
('SUP-011','ThyssenKrupp Supply','Germany',20,4.4),
('SUP-012','Continental Parts AG','Germany',17,4.5),
('SUP-013','GE Supply Chain','USA',22,4.3),
('SUP-014','Honeywell Materials','USA',20,4.6),
('SUP-015','3M Industrial Supply','USA',19,4.1),
('SUP-016','Caterpillar Parts','USA',25,3.7),
('SUP-017','Foxconn Components','China',10,4.0),
('SUP-018','BYD Supply Co','China',11,4.2),
('SUP-019','Huawei Industrial','China',9,3.9),
('SUP-020','CRRC Materials','China',13,4.1);

-- ============================================================
-- 2. DIM_PLANT  (5 rows)
-- ============================================================
INSERT INTO DIM_PLANT VALUES
('PLT-001','Dubai Manufacturing Hub','Dubai','UAE',50000),
('PLT-002','Abu Dhabi Assembly','Abu Dhabi','UAE',35000),
('PLT-003','Mumbai Production Center','Mumbai','India',45000),
('PLT-004','Chennai Electronics Plant','Chennai','India',40000),
('PLT-005','Frankfurt Precision Works','Frankfurt','Germany',30000);

-- ============================================================
-- 3. DIM_CUSTOMER  (25 rows across industries and tiers)
-- ============================================================
INSERT INTO DIM_CUSTOMER VALUES
('CUST-001','ADNOC','Oil & Gas','UAE','Platinum'),
('CUST-002','Emirates Airlines','Aviation','UAE','Platinum'),
('CUST-003','Etisalat','Telecom','UAE','Gold'),
('CUST-004','Dubai Electricity (DEWA)','Utilities','UAE','Gold'),
('CUST-005','DP World','Logistics','UAE','Platinum'),
('CUST-006','Tata Motors','Automotive','India','Gold'),
('CUST-007','Infosys','Technology','India','Silver'),
('CUST-008','Larsen & Toubro','Construction','India','Gold'),
('CUST-009','Wipro Technologies','Technology','India','Silver'),
('CUST-010','Reliance Industries','Conglomerate','India','Platinum'),
('CUST-011','BMW Group','Automotive','Germany','Platinum'),
('CUST-012','Deutsche Telekom','Telecom','Germany','Gold'),
('CUST-013','BASF Chemical','Chemical','Germany','Gold'),
('CUST-014','Volkswagen','Automotive','Germany','Platinum'),
('CUST-015','SAP SE','Technology','Germany','Silver'),
('CUST-016','Tesla Inc','Automotive','USA','Platinum'),
('CUST-017','Amazon Logistics','Technology','USA','Gold'),
('CUST-018','Boeing Company','Aviation','USA','Platinum'),
('CUST-019','Walmart Supply','Retail','USA','Gold'),
('CUST-020','General Motors','Automotive','USA','Gold'),
('CUST-021','Alibaba Group','Technology','China','Gold'),
('CUST-022','SAIC Motor','Automotive','China','Silver'),
('CUST-023','Huawei Technologies','Telecom','China','Gold'),
('CUST-024','BYD Auto','Automotive','China','Silver'),
('CUST-025','PetroChina','Oil & Gas','China','Platinum');

-- ============================================================
-- 4. DIM_PART  (30 rows across 4 categories)
-- ============================================================
INSERT INTO DIM_PART VALUES
('PRT-001','Circuit Board A1','ELECTRONICS',45.00,'SUP-017','PLT-004'),
('PRT-002','Sensor Module X','ELECTRONICS',120.50,'SUP-009','PLT-005'),
('PRT-003','Power Controller','ELECTRONICS',89.00,'SUP-004','PLT-004'),
('PRT-004','LED Display Panel','ELECTRONICS',210.00,'SUP-017','PLT-004'),
('PRT-005','Microprocessor Unit','ELECTRONICS',350.00,'SUP-009','PLT-005'),
('PRT-006','Capacitor Array','ELECTRONICS',15.75,'SUP-019','PLT-004'),
('PRT-007','Fiber Optic Cable','ELECTRONICS',55.00,'SUP-014','PLT-001'),
('PRT-008','Bearing Assembly','MECHANICAL',32.00,'SUP-010','PLT-005'),
('PRT-009','Hydraulic Pump','MECHANICAL',475.00,'SUP-011','PLT-005'),
('PRT-010','Gear Box Unit','MECHANICAL',280.00,'SUP-001','PLT-003'),
('PRT-011','Steel Shaft','MECHANICAL',65.00,'SUP-001','PLT-003'),
('PRT-012','Brake Assembly','MECHANICAL',190.00,'SUP-010','PLT-005'),
('PRT-013','Drive Belt','MECHANICAL',22.50,'SUP-002','PLT-003'),
('PRT-014','Valve Actuator','MECHANICAL',145.00,'SUP-005','PLT-001'),
('PRT-015','Compressor Unit','MECHANICAL',520.00,'SUP-011','PLT-005'),
('PRT-016','Corrugated Box Large','PACKAGING',3.50,'SUP-003','PLT-003'),
('PRT-017','Foam Insert Custom','PACKAGING',8.25,'SUP-003','PLT-003'),
('PRT-018','Pallet Wrap Industrial','PACKAGING',12.00,'SUP-007','PLT-001'),
('PRT-019','Anti-Static Bag','PACKAGING',1.75,'SUP-019','PLT-004'),
('PRT-020','Wooden Crate Medium','PACKAGING',18.00,'SUP-006','PLT-001'),
('PRT-021','Shrink Wrap Roll','PACKAGING',6.50,'SUP-007','PLT-002'),
('PRT-022','Aluminum Ingot','RAW_MATERIAL',85.00,'SUP-005','PLT-001'),
('PRT-023','Copper Wire Spool','RAW_MATERIAL',110.00,'SUP-018','PLT-004'),
('PRT-024','Steel Plate 10mm','RAW_MATERIAL',95.00,'SUP-001','PLT-003'),
('PRT-025','Polymer Resin','RAW_MATERIAL',42.00,'SUP-013','PLT-002'),
('PRT-026','Carbon Fiber Sheet','RAW_MATERIAL',320.00,'SUP-015','PLT-001'),
('PRT-027','Titanium Rod','RAW_MATERIAL',450.00,'SUP-012','PLT-005'),
('PRT-028','Rubber Compound','RAW_MATERIAL',28.00,'SUP-002','PLT-003'),
('PRT-029','Glass Panel Tempered','RAW_MATERIAL',75.00,'SUP-008','PLT-002'),
('PRT-030','Silicone Sealant','RAW_MATERIAL',16.00,'SUP-006','PLT-001');

-- ============================================================
-- 5. FCT_PURCHASE_ORDERS  (500 rows, ~15% late delivery)
--    Uses GENERATOR + controlled randomness
-- ============================================================
INSERT INTO FCT_PURCHASE_ORDERS
WITH supplier_list AS (
    SELECT supplier_id, country, lead_time_days FROM DIM_SUPPLIER
),
part_list AS (
    SELECT part_id, unit_cost, supplier_id, plant_id FROM DIM_PART
),
base AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) AS rn,
        UNIFORM(1, 30, RANDOM()) AS part_idx,
        UNIFORM(1, 20, RANDOM()) AS sup_idx,
        UNIFORM(1, 5, RANDOM()) AS plant_idx,
        UNIFORM(50, 500, RANDOM()) AS order_qty,
        UNIFORM(1, 100, RANDOM()) AS late_pct_rand,
        UNIFORM(1, 100, RANDOM()) AS status_rand,
        UNIFORM(0, 180, RANDOM()) AS day_offset,
        UNIFORM(5, 30, RANDOM()) AS lead_days,
        UNIFORM(1, 100, RANDOM()) AS recv_pct_rand
    FROM TABLE(GENERATOR(ROWCOUNT => 500))
),
enriched AS (
    SELECT
        b.rn,
        'PO-' || LPAD(b.rn, 4, '0') AS po_id,
        'PRT-' || LPAD(b.part_idx, 3, '0') AS part_id,
        'SUP-' || LPAD(b.sup_idx, 3, '0') AS supplier_id,
        'PLT-' || LPAD(b.plant_idx, 3, '0') AS plant_id,
        b.order_qty,
        p.unit_cost AS unit_cost_ea,
        ROUND(p.unit_cost * b.order_qty * UNIFORM(2,8, RANDOM()) / 100, 2) AS freight_cost,
        ROUND(p.unit_cost * b.order_qty * UNIFORM(1,5, RANDOM()) / 100, 2) AS customs_tariff_cost,
        DATEADD('day', -b.day_offset, '2026-09-27'::DATE) AS order_date,
        b.lead_days,
        b.late_pct_rand,
        b.status_rand,
        b.recv_pct_rand,
        b.order_qty AS oq
    FROM base b
    JOIN part_list p ON p.part_id = 'PRT-' || LPAD(b.part_idx, 3, '0')
)
SELECT
    po_id,
    part_id,
    supplier_id,
    plant_id,
    order_qty,
    CASE
        WHEN status_rand <= 10 THEN NULL                          -- 10% open/pending
        WHEN recv_pct_rand <= 8 THEN ROUND(order_qty * 0.85)     -- 8% partial receipt
        ELSE order_qty
    END AS received_qty,
    unit_cost_ea,
    freight_cost,
    customs_tariff_cost,
    DATEADD('day', lead_days, order_date) AS promised_date,
    CASE
        WHEN status_rand <= 10 THEN NULL                          -- open orders
        WHEN late_pct_rand <= 15                                  -- 15% late
            THEN DATEADD('day', lead_days + UNIFORM(1, 12, RANDOM()), order_date)
        ELSE DATEADD('day', lead_days - UNIFORM(0, 3, RANDOM()), order_date)
    END AS receipt_date,
    CASE
        WHEN status_rand <= 10 THEN 'OPEN'
        WHEN status_rand <= 15 THEN 'PARTIALLY_RECEIVED'
        ELSE 'RECEIVED'
    END AS po_status
FROM enriched;

-- ============================================================
-- 6. FCT_SHIPMENTS  (600 rows, ~8% carrier transit delay)
-- ============================================================
INSERT INTO FCT_SHIPMENTS
WITH po_list AS (
    SELECT po_id, plant_id, promised_date FROM FCT_PURCHASE_ORDERS
),
carriers AS (
    SELECT column1 AS carrier_name FROM VALUES
        ('Maersk'),('DHL Logistics'),('FedEx Freight'),('Aramex'),
        ('DB Schenker'),('Emirates SkyCargo'),('CMA CGM'),('Kuehne+Nagel')
),
base AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) AS rn,
        UNIFORM(1, 500, RANDOM()) AS po_idx,
        UNIFORM(1, 8, RANDOM()) AS carrier_idx,
        UNIFORM(1, 5, RANDOM()) AS origin_idx,
        UNIFORM(1, 5, RANDOM()) AS dest_idx,
        UNIFORM(3, 21, RANDOM()) AS transit_days,
        UNIFORM(1, 100, RANDOM()) AS delay_rand,
        UNIFORM(1, 100, RANDOM()) AS status_rand
    FROM TABLE(GENERATOR(ROWCOUNT => 600))
),
carrier_numbered AS (
    SELECT carrier_name, ROW_NUMBER() OVER (ORDER BY carrier_name) AS cidx FROM carriers
)
SELECT
    'SHP-' || LPAD(b.rn, 4, '0') AS ship_id,
    'PO-' || LPAD(b.po_idx, 4, '0') AS po_id,
    c.carrier_name,
    'PLT-' || LPAD(b.origin_idx, 3, '0') AS origin_plant_id,
    'PLT-' || LPAD(
        CASE WHEN b.dest_idx = b.origin_idx
             THEN MOD(b.dest_idx, 5) + 1
             ELSE b.dest_idx END, 3, '0') AS dest_plant_id,
    DATEADD('day', -UNIFORM(0, 180, RANDOM()), '2026-09-27'::DATE) AS ship_date,
    DATEADD('day', b.transit_days,
        DATEADD('day', -UNIFORM(0, 180, RANDOM()), '2026-09-27'::DATE)) AS estimated_delivery_date,
    CASE
        WHEN status_rand <= 12 THEN NULL                          -- 12% in transit
        WHEN delay_rand <= 8                                      -- 8% delayed
            THEN DATEADD('day', b.transit_days + UNIFORM(2, 10, RANDOM()),
                 DATEADD('day', -UNIFORM(0, 180, RANDOM()), '2026-09-27'::DATE))
        ELSE DATEADD('day', b.transit_days - UNIFORM(0, 2, RANDOM()),
             DATEADD('day', -UNIFORM(0, 180, RANDOM()), '2026-09-27'::DATE))
    END AS actual_delivery_date,
    CASE
        WHEN status_rand <= 12 THEN 'IN_TRANSIT'
        WHEN delay_rand <= 8 THEN 'DELIVERED_LATE'
        ELSE 'DELIVERED'
    END AS transit_status
FROM base b
JOIN carrier_numbered c ON c.cidx = b.carrier_idx;

-- ============================================================
-- 7. FCT_CUSTOMER_ORDERS  (800 rows, ~12% late, ~5% partial fill)
-- ============================================================
INSERT INTO FCT_CUSTOMER_ORDERS
WITH base AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) AS rn,
        UNIFORM(1, 25, RANDOM()) AS cust_idx,
        UNIFORM(1, 30, RANDOM()) AS part_idx,
        UNIFORM(1, 5, RANDOM()) AS plant_idx,
        UNIFORM(10, 300, RANDOM()) AS ordered_qty,
        UNIFORM(1, 100, RANDOM()) AS late_rand,
        UNIFORM(1, 100, RANDOM()) AS partial_rand,
        UNIFORM(1, 100, RANDOM()) AS status_rand,
        UNIFORM(0, 180, RANDOM()) AS day_offset,
        UNIFORM(5, 20, RANDOM()) AS fulfill_days
    FROM TABLE(GENERATOR(ROWCOUNT => 800))
)
SELECT
    'ORD-' || LPAD(rn, 4, '0') AS order_id,
    'CUST-' || LPAD(cust_idx, 3, '0') AS customer_id,
    'PRT-' || LPAD(part_idx, 3, '0') AS part_id,
    'PLT-' || LPAD(plant_idx, 3, '0') AS plant_id,
    ordered_qty,
    CASE
        WHEN status_rand <= 8 THEN NULL                           -- 8% not yet shipped
        WHEN partial_rand <= 5 THEN ROUND(ordered_qty * 0.80)    -- 5% partial fill
        ELSE ordered_qty
    END AS shipped_qty,
    DATEADD('day', -day_offset, '2026-09-27'::DATE) AS request_date,
    CASE
        WHEN status_rand <= 8 THEN NULL                           -- not shipped yet
        WHEN late_rand <= 12                                      -- 12% late
            THEN DATEADD('day', fulfill_days + UNIFORM(3, 15, RANDOM()),
                 DATEADD('day', -day_offset, '2026-09-27'::DATE))
        ELSE DATEADD('day', fulfill_days,
             DATEADD('day', -day_offset, '2026-09-27'::DATE))
    END AS shipped_date,
    CASE
        WHEN status_rand <= 8 THEN 'PENDING'
        WHEN late_rand <= 12 THEN 'DELIVERED_LATE'
        WHEN partial_rand <= 5 THEN 'PARTIAL_FILL'
        ELSE 'DELIVERED'
    END AS delivery_status
FROM base;
