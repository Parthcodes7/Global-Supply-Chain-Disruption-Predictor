-- =====================================================================
-- Global Supply Chain Disruption Predictor
-- Database Schema Definition (Core DDL - Step 1 MVP)
-- Target RDBMS: MySQL 8.0+
-- Strict Scope: No CTEs, No Window Functions, No JSON Functions
-- =====================================================================

DROP DATABASE IF EXISTS supply_chain_db;
CREATE DATABASE supply_chain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE supply_chain_db;

-- ---------------------------------------------------------------------
-- 1. PORTS TABLE (Primary Spatial Nodes)
-- ---------------------------------------------------------------------
CREATE TABLE PORTS (
    port_code INT PRIMARY KEY,
    port_name VARCHAR(150) NOT NULL,
    country_code VARCHAR(100) NOT NULL,
    un_locode VARCHAR(20),
    region_name VARCHAR(150),
    harbor_size VARCHAR(50) DEFAULT 'Medium',
    harbor_type VARCHAR(50) DEFAULT 'Coastal (Natural)',
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    location POINT SRID 4326 NOT NULL,
    status VARCHAR(30) DEFAULT 'Operational',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SPATIAL INDEX(location)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. DISASTERS TABLE (Natural Disasters & Hazards)
-- ---------------------------------------------------------------------
CREATE TABLE DISASTERS (
    disaster_id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity_level INT DEFAULT 1,
    alert_level VARCHAR(20) DEFAULT 'Green',
    start_time DATETIME,
    end_time DATETIME,
    country VARCHAR(255),
    iso3 VARCHAR(10),
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    location POINT SRID 4326 NOT NULL,
    radius_km DOUBLE DEFAULT 300.0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SPATIAL INDEX(location)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. CONFLICTS TABLE (Geopolitical Risk & Instability)
-- ---------------------------------------------------------------------
CREATE TABLE CONFLICTS (
    conflict_id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    recorded_month DATE,
    instability_score DECIMAL(6, 2) DEFAULT 0.00,
    political_stability_index DECIMAL(6, 4) DEFAULT 0.0000,
    sanctions_active TINYINT(1) DEFAULT 0,
    protest_events_last_3m INT DEFAULT 0,
    conflict_escalation_6m TINYINT(1) DEFAULT 0,
    regime_type VARCHAR(50) DEFAULT 'Democracy',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conflict_country (country)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. COMMODITIES TABLE (Cargo Valuations)
-- ---------------------------------------------------------------------
CREATE TABLE COMMODITIES (
    commodity_id INT AUTO_INCREMENT PRIMARY KEY,
    commodity_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    avg_price_usd DECIMAL(12, 4) NOT NULL,
    annual_change_pct DECIMAL(6, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_commodity_name (commodity_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. SHIPMENTS TABLE (Relational Movement Records)
-- ---------------------------------------------------------------------
CREATE TABLE SHIPMENTS (
    shipment_id INT AUTO_INCREMENT PRIMARY KEY,
    tracking_number VARCHAR(50) UNIQUE NOT NULL,
    vessel_name VARCHAR(100) NOT NULL,
    origin_port_id INT NOT NULL,
    destination_port_id INT NOT NULL,
    commodity_id INT,
    cargo_weight_tonnes DECIMAL(12, 2) DEFAULT 1000.00,
    estimated_value_usd DECIMAL(15, 2) DEFAULT 500000.00,
    departure_date DATETIME NOT NULL,
    estimated_arrival DATETIME NOT NULL,
    status VARCHAR(30) DEFAULT 'In Transit',
    risk_level VARCHAR(20) DEFAULT 'Low',
    disruption_notes VARCHAR(255) DEFAULT 'Normal Transit',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_origin_port FOREIGN KEY (origin_port_id) REFERENCES PORTS(port_code) ON DELETE CASCADE,
    CONSTRAINT fk_destination_port FOREIGN KEY (destination_port_id) REFERENCES PORTS(port_code) ON DELETE CASCADE,
    CONSTRAINT fk_commodity FOREIGN KEY (commodity_id) REFERENCES COMMODITIES(commodity_id) ON DELETE SET NULL,
    INDEX idx_shipment_status (status),
    INDEX idx_shipment_dest (destination_port_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. DISRUPTION_LOG TABLE (Audit Trail for Triggers & Events)
-- ---------------------------------------------------------------------
CREATE TABLE DISRUPTION_LOG (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    disaster_id INT,
    affected_port_code INT,
    affected_shipment_id INT,
    distance_km DOUBLE,
    action_taken VARCHAR(255),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
