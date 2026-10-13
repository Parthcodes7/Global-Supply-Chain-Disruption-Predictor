# Antigravity Automation Instructions: Global Supply Chain Disruption Predictor

## 1. Project Overview & Mechanics
**What it is:** An academic project prototype (VIT, Pune) designed to track global maritime ports, active shipping routes, natural disasters, and geopolitical conflicts in a relational spatial database.
**How it works:** The system maps global ports and shipments. When a disruption (like a natural disaster or conflict) is logged, the database uses GIS spatial queries (`ST_Distance_Sphere`, `ST_Contains`) combined with standard relational logic to identify which ports and shipments are at risk, allowing for automated status updates and route alternatives.

## 2. Project Scope (50% Completion Goal)
**CRITICAL INSTRUCTION:** Do not attempt to build a 100% complete, production-ready system. The objective is to build exactly **50% of the project**—a functional Minimum Viable Prototype (MVP). 
*   We only need core tables, partial data ingestion (enough to prove the concept), and a limited set of demonstration queries, triggers, and procedures.
*   Do not over-engineer error handling or build a front-end UI. Stick to backend database architecture and CLI demonstration.

## 3. Action Plan (MVP Path)
Execute the following steps sequentially via the MySQL CLI:
*   **Step 1: Core DDL (Schema Build):** Create the `PORTS`, `SHIPMENTS`, `DISASTERS`, and `CONFLICTS` tables. Ensure `PORTS` has the `location POINT SRID 4326` column and spatial index.
*   **Step 2: MVP Data Ingestion:** Write basic Python/CLI automation to load a sample subset of data from `UpdatedPub150.csv`, `all_disasters_merged.csv`, `geopolitical_conflict_risk_dataset.csv`, and `all_commodities_merged.csv`. (Do not worry if some edge-case rows fail; aim for a working sample).
*   **Step 3: Core Business Logic (Queries):** Write 3-4 complex `SELECT` statements demonstrating joins, subqueries, group by, and spatial distance to find shipments affected by a specific disaster.
*   **Step 4: Active DB Features:** Create exactly ONE Stored Procedure (e.g., `Find_Alternative_Port`) and ONE Trigger (e.g., `Update_Shipment_Status_On_Disaster`) to demonstrate automation.

## 4. Execution Environment & Automation Protocol
* **Interface:** All SQL commands must be executed via the MySQL Command Line Client (`mysql`).
* **Automation Method:** Generate `.sql` script files and execute them automatically using bash commands (e.g., `mysql -u [user] -p[pass] [db] < script.sql`).

## 5. Strict SQL Scope Restrictions
You are strictly limited to the following SQL concepts. **DO NOT** use window functions, CTEs, or JSON functions:
*   **DDL/DML:** `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`.
*   **Views:** `CREATE VIEW`, `DROP VIEW`.
*   **Filtering:** `=`, `<`, `>`, `<=`, `>=`, `<>`, `AND`, `OR`, `NOT`, `LIKE`, `NOT LIKE`, `IN`, `NOT IN`, `BETWEEN ... AND`, `IS NULL`, `IS NOT NULL`.
*   **Aggregation:** `ORDER BY`, `GROUP BY`, `COUNT()`, `SUM()`, `AVG()`, `MAX()`, `MIN()`, `HAVING`.
*   **Relational:** `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `CROSS JOIN`.
*   **Set Operators:** `UNION`, `UNION ALL`.
*   **Subqueries:** Nested Queries and Correlated Queries.
*   **Active Logic:** `CREATE TRIGGER`, `CREATE PROCEDURE`, `CALL`.