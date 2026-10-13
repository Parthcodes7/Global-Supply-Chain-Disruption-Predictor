-- =====================================================================
-- Global Supply Chain Disruption Predictor
-- Stored Procedures & Triggers (Step 4 MVP)
-- Target RDBMS: MySQL 8.0+
-- Strict Scope: No CTEs, No Window Functions, No JSON Functions
-- =====================================================================

USE supply_chain_db;

DELIMITER $$

-- ---------------------------------------------------------------------
-- Trigger: Automated Port & Shipment Disruption Alert on Disaster Insert
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_after_disaster_insert$$
CREATE TRIGGER trg_after_disaster_insert
AFTER INSERT ON DISASTERS
FOR EACH ROW
BEGIN
    -- 1. Update ports falling within the hazard radius to 'Hazard Alert'
    UPDATE PORTS p
    SET p.status = 'Hazard Alert'
    WHERE ST_Distance_Sphere(p.location, NEW.location) <= (NEW.radius_km * 1000);

    -- 2. Automatically disrupt active shipments heading to or originating from affected ports
    UPDATE SHIPMENTS s
    INNER JOIN PORTS p ON s.destination_port_id = p.port_code OR s.origin_port_id = p.port_code
    SET s.status = 'Disrupted',
        s.risk_level = 'Critical',
        s.disruption_notes = CONCAT('Disrupted by ', NEW.event_type, ' (', NEW.alert_level, ' alert) within ', ROUND(NEW.radius_km), 'km')
    WHERE s.status = 'In Transit'
      AND ST_Distance_Sphere(p.location, NEW.location) <= (NEW.radius_km * 1000);

    -- 3. Write an audit log entry for this automated safety intervention
    INSERT INTO DISRUPTION_LOG (disaster_id, affected_port_code, affected_shipment_id, distance_km, action_taken)
    SELECT 
        NEW.disaster_id,
        p.port_code,
        s.shipment_id,
        ROUND(ST_Distance_Sphere(p.location, NEW.location) / 1000, 2),
        CONCAT('Automated reroute required for vessel ', s.vessel_name)
    FROM PORTS p
    LEFT JOIN SHIPMENTS s ON s.destination_port_id = p.port_code AND s.status = 'Disrupted'
    WHERE ST_Distance_Sphere(p.location, NEW.location) <= (NEW.radius_km * 1000);
END$$

-- ---------------------------------------------------------------------
-- Stored Procedure: Find Safe Alternative Rerouting Port
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_find_alternative_port$$
CREATE PROCEDURE sp_find_alternative_port(
    IN p_disrupted_port_code INT,
    IN p_search_radius_km DOUBLE
)
BEGIN
    DECLARE v_orig_lat DECIMAL(10, 6);
    DECLARE v_orig_lon DECIMAL(10, 6);
    DECLARE v_orig_loc POINT;
    DECLARE v_orig_name VARCHAR(150);

    -- Fetch original port coordinates
    SELECT port_name, location, latitude, longitude
    INTO v_orig_name, v_orig_loc, v_orig_lat, v_orig_lon
    FROM PORTS
    WHERE port_code = p_disrupted_port_code
    LIMIT 1;

    -- Query alternative operational ports within search radius free from active hazards
    SELECT 
        p.port_code,
        p.port_name,
        p.country_code,
        p.harbor_size,
        p.harbor_type,
        p.latitude,
        p.longitude,
        ROUND(ST_Distance_Sphere(p.location, v_orig_loc) / 1000, 2) AS distance_from_disrupted_km,
        COALESCE(c.instability_score, 0.0) AS political_risk_score,
        'Recommended Safe Alternative' AS recommendation_status
    FROM PORTS p
    LEFT JOIN CONFLICTS c ON p.country_code = c.country
    WHERE p.port_code <> p_disrupted_port_code
      AND p.status = 'Operational'
      AND (ST_Distance_Sphere(p.location, v_orig_loc) / 1000) <= p_search_radius_km
      AND NOT EXISTS (
          -- Ensure alternative port is not within danger perimeter of any active disaster
          SELECT 1 
          FROM DISASTERS d 
          WHERE ST_Distance_Sphere(p.location, d.location) <= (d.radius_km * 1000)
      )
    ORDER BY distance_from_disrupted_km ASC
    LIMIT 10;
END$$

DELIMITER ;
