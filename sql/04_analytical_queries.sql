-- =====================================================================
-- Global Supply Chain Disruption Predictor
-- Comprehensive Academic Query Suite (VIT Pune DBMS Evaluation)
-- Covers: DDL, DML, Views, Joins, Conditionals, Logical, LIKE/NOT LIKE,
--         IN/NOT IN, BETWEEN...AND, IS NULL/IS NOT NULL, ORDER BY,
--         GROUP BY, COUNT/SUM/AVG/MIN/MAX, HAVING, UNION/UNION ALL,
--         Nested Subqueries, Correlated Subqueries, Triggers, Procedures
-- =====================================================================

USE supply_chain_db;

-- ---------------------------------------------------------------------
-- QUERY 1: Spatial Proximity & Pattern Filtering
-- Demonstrates: INNER JOIN, LEFT JOIN, LIKE, NOT LIKE, IS NOT NULL,
--               AND, OR, ORDER BY, ST_Distance_Sphere
-- ---------------------------------------------------------------------
SELECT 
    s.tracking_number,
    s.vessel_name,
    p.port_name AS destination_port,
    p.country_code,
    p.harbor_type,
    d.event_type AS hazard_event,
    d.alert_level,
    ROUND(ST_Distance_Sphere(p.location, d.location) / 1000, 2) AS distance_km,
    s.estimated_value_usd
FROM SHIPMENTS s
INNER JOIN PORTS p ON s.destination_port_id = p.port_code
INNER JOIN DISASTERS d ON ST_Distance_Sphere(p.location, d.location) <= (d.radius_km * 1000)
LEFT JOIN COMMODITIES c ON s.commodity_id = c.commodity_id
WHERE (p.harbor_type LIKE '%Coastal%' OR p.harbor_type LIKE '%River%')
  AND p.port_name NOT LIKE '%Air%'
  AND s.disruption_notes IS NOT NULL
ORDER BY distance_km ASC;

-- ---------------------------------------------------------------------
-- QUERY 2: Multi-Aggregation & Exposure Grouping
-- Demonstrates: GROUP BY, HAVING, COUNT(), SUM(), AVG(), MIN(), MAX(),
--               BETWEEN ... AND, INNER JOIN, LEFT JOIN, ORDER BY
-- ---------------------------------------------------------------------
SELECT 
    p.country_code AS destination_country,
    COALESCE(c.commodity_name, 'Bulk Miscellaneous') AS commodity_name,
    COUNT(s.shipment_id) AS total_shipments,
    SUM(s.cargo_weight_tonnes) AS total_tonnes_at_risk,
    SUM(s.estimated_value_usd) AS total_value_at_risk_usd,
    AVG(s.estimated_value_usd) AS avg_value_usd,
    MIN(s.estimated_value_usd) AS min_shipment_value_usd,
    MAX(s.estimated_value_usd) AS max_shipment_value_usd
FROM SHIPMENTS s
INNER JOIN PORTS p ON s.destination_port_id = p.port_code
LEFT JOIN COMMODITIES c ON s.commodity_id = c.commodity_id
WHERE s.cargo_weight_tonnes BETWEEN 5000.00 AND 90000.00
  AND s.status IN ('In Transit', 'Disrupted')
GROUP BY p.country_code, c.commodity_name
HAVING SUM(s.estimated_value_usd) >= 500000.00
ORDER BY total_value_at_risk_usd DESC;

-- ---------------------------------------------------------------------
-- QUERY 3: Advanced Subqueries (Nested & Correlated)
-- Demonstrates: Nested Subquery, Correlated Subquery, NOT IN,
--               IS NOT NULL, Subquery in WHERE, Subquery in SELECT
-- ---------------------------------------------------------------------
SELECT 
    s.tracking_number,
    s.vessel_name,
    dp.port_name AS destination_port,
    dp.country_code,
    s.cargo_weight_tonnes,
    s.estimated_value_usd,
    -- Correlated Subquery: counts how many other vessels are heading to the same port
    (
        SELECT COUNT(*) 
        FROM SHIPMENTS s2 
        WHERE s2.destination_port_id = s.destination_port_id
    ) AS total_traffic_at_destination
FROM SHIPMENTS s
INNER JOIN PORTS dp ON s.destination_port_id = dp.port_code
WHERE dp.country_code NOT IN ('Unknown', 'Disputed')
  AND s.disruption_notes IS NOT NULL
  AND s.estimated_value_usd > (
      -- Nested Subquery: shipments with value above global average shipment value
      SELECT AVG(estimated_value_usd) 
      FROM SHIPMENTS
  )
ORDER BY s.estimated_value_usd DESC;

-- ---------------------------------------------------------------------
-- QUERY 4: Set Operator UNION
-- Demonstrates: UNION (Combining Disaster Zones with Sanctioned Countries)
-- ---------------------------------------------------------------------
SELECT 
    p.port_code,
    p.port_name,
    p.country_code,
    'NATURAL_DISASTER_HAZARD' AS chokepoint_type,
    d.event_type AS hazard_details,
    d.alert_level AS risk_grade
FROM PORTS p
INNER JOIN DISASTERS d ON ST_Distance_Sphere(p.location, d.location) <= (d.radius_km * 1000)

UNION

SELECT 
    p.port_code,
    p.port_name,
    p.country_code,
    'GEOPOLITICAL_SANCTIONS' AS chokepoint_type,
    CONCAT('Regime: ', cf.regime_type, ' (Score: ', cf.instability_score, ')') AS hazard_details,
    'Active Sanction' AS risk_grade
FROM PORTS p
INNER JOIN CONFLICTS cf ON p.country_code = cf.country
WHERE cf.sanctions_active = 1 OR cf.conflict_escalation_6m = 1

ORDER BY chokepoint_type, port_name;
