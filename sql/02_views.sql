-- =====================================================================
-- Global Supply Chain Disruption Predictor
-- Database Views (Standard Relational Views - Step 1 MVP)
-- Strict Scope: No CTEs, No Window Functions, No JSON Functions
-- =====================================================================

USE supply_chain_db;

-- ---------------------------------------------------------------------
-- View 1: Active Disrupted Shipments Detailed Overview
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_disrupted_shipments AS
SELECT 
    s.shipment_id,
    s.tracking_number,
    s.vessel_name,
    s.status,
    s.risk_level,
    s.disruption_notes,
    op.port_name AS origin_port,
    op.country_code AS origin_country,
    dp.port_name AS destination_port,
    dp.country_code AS destination_country,
    c.commodity_name,
    s.cargo_weight_tonnes,
    s.estimated_value_usd,
    s.departure_date,
    s.estimated_arrival
FROM SHIPMENTS s
INNER JOIN PORTS op ON s.origin_port_id = op.port_code
INNER JOIN PORTS dp ON s.destination_port_id = dp.port_code
LEFT JOIN COMMODITIES c ON s.commodity_id = c.commodity_id
WHERE s.status IN ('Disrupted', 'Delayed', 'Diverted');

-- ---------------------------------------------------------------------
-- View 2: Ports Under Critical Environmental / Geopolitical Threat
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_high_risk_ports AS
SELECT 
    p.port_code,
    p.port_name,
    p.country_code,
    p.harbor_size,
    p.status AS port_status,
    p.latitude,
    p.longitude,
    COALESCE(cf.instability_score, 0.0) AS country_instability,
    COALESCE(cf.regime_type, 'Unknown') AS regime_type,
    COALESCE(cf.sanctions_active, 0) AS has_sanctions
FROM PORTS p
LEFT JOIN CONFLICTS cf ON p.country_code = cf.country
WHERE p.status = 'Hazard Alert' 
   OR cf.instability_score >= 70.0
   OR cf.sanctions_active = 1;

-- ---------------------------------------------------------------------
-- View 3: Financial Exposure Summary by Commodity
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_commodity_exposure AS
SELECT 
    COALESCE(c.commodity_name, 'General Cargo') AS commodity_name,
    COUNT(s.shipment_id) AS total_affected_shipments,
    SUM(s.cargo_weight_tonnes) AS total_tonnes_at_risk,
    SUM(s.estimated_value_usd) AS total_value_at_risk_usd,
    AVG(s.estimated_value_usd) AS avg_shipment_value_usd
FROM SHIPMENTS s
LEFT JOIN COMMODITIES c ON s.commodity_id = c.commodity_id
WHERE s.status = 'Disrupted'
GROUP BY c.commodity_name;
