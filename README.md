# 🚢 Global Supply Chain Disruption Predictor

An academic Database Management Systems (DBMS) prototype developed for **VIT Pune**, powered by **MySQL 8.0 Spatial Engine** and **FastAPI**. 

This system models real-time maritime logistics vulnerabilities by correlating global shipping voyages against natural disasters (cyclones, earthquakes, tsunamis) and geopolitical conflict risk zones.

---

## 📌 Project Highlights & Academic Syllabus Compliance

This project demonstrates all standard academic relational database syllabus concepts:

* **DDL (Data Definition Language):** Defined in [`sql/01_schema.sql`](sql/01_schema.sql) with Primary Keys, Foreign Keys, Spatial `POINT SRID 4326` data types, and `SPATIAL INDEX`.
* **DML (Data Manipulation Language):** Live CRUD operations directly persisted into MySQL:
  * **INSERT:** Add new voyages via the dashboard modal (`INSERT INTO SHIPMENTS ...`).
  * **UPDATE:** Modify vessel status, cargo value, and notes (`UPDATE SHIPMENTS SET ...`).
  * **DELETE:** Remove cancelled shipments (`DELETE FROM SHIPMENTS WHERE ...`).
* **WHERE Clause Operators:**
  * Pattern Matching: `LIKE` / `NOT LIKE`
  * Set Membership: `IN` / `NOT IN`
  * Range Searching: `BETWEEN ... AND`
  * Null Testing: `IS NULL` / `IS NOT NULL`
* **Relational Views:** Defined in [`sql/02_views.sql`](sql/02_views.sql):
  * `v_disrupted_shipments`: Real-time view of delayed, diverted, and disrupted voyages.
  * `v_high_risk_ports`: Environmental and geopolitical threat assessment.
  * `v_commodity_exposure`: Financial aggregation of at-risk commodities.
* **Aggregations & Grouping:** `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()` with `GROUP BY` and `HAVING` clauses.
* **Subqueries:**
  * **Nested Subqueries** in `WHERE` clauses.
  * **Correlated Subqueries** in `SELECT` clauses.
* **Set Operators:** `UNION` combining environmental chokepoints and conflict zones.
* **Triggers:**
  * `trg_after_disaster_insert`: An `AFTER INSERT` trigger on `DISASTERS` that automatically recalculates spherical hazard distance (`ST_Distance_Sphere`), transitions nearby ports to `Hazard Alert`, disrupts active shipments, and writes audit records to `DISRUPTION_LOG`.
* **Stored Procedures:**
  * `sp_find_alternative_port`: Evaluates disrupted destination ports and queries the nearest operational ports outside active disaster perimeters.

---

## 📂 Datasets Integrated

The database is pre-seeded with 4 real-world datasets:
1. `UpdatedPub150.csv` &rarr; Ingested into `PORTS` (250 sample global ports with coordinates and harbor classifications).
2. `all_commodities_merged.csv` &rarr; Ingested into `COMMODITIES` (35 commodity categories with unit pricing).
3. `geopolitical_conflict_risk_dataset.csv` &rarr; Ingested into `CONFLICTS` (120 country-level instability metrics).
4. `all_disasters_merged.csv` &rarr; Ingested into `DISASTERS` (100+ natural hazard events with impact radii).

---

## 🏗️ Repository Architecture

```text
├── UpdatedPub150.csv                     # Raw Ports dataset
├── all_commodities_merged.csv            # Raw Commodities dataset
├── all_disasters_merged.csv              # Raw Disasters dataset
├── geopolitical_conflict_risk_dataset.csv# Raw Geopolitical Risk dataset
├── run_project.bat                       # 1-Click launcher (starts MySQL & Dashboard)
├── run_pipeline.bat                      # Runs all SQL automation scripts via CLI
├── open_mysql_cli.bat                    # Interactive MySQL 8.0 command-line client
├── requirements.txt                      # Python dependencies
├── backend/
│   └── server.py                         # FastAPI REST API & Static File Server
├── frontend/
│   ├── index.html                        # Academic Portal UI with Live CRUD
│   ├── app.js                            # Frontend JavaScript logic & API connectors
│   └── style.css                         # Dark aesthetic design system
├── sql/
│   ├── 01_schema.sql                     # Table schemas, spatial indices & constraints
│   ├── 02_views.sql                      # Academic SQL relational views
│   ├── 03_procedures_triggers.sql        # Triggers and stored procedures
│   ├── 02_sample_data.sql                # Seed data extracted from CSVs
│   └── 04_analytical_queries.sql         # 4 syllabus queries (Joins, Aggregates, Subqueries, UNION)
└── scripts/
    ├── prepare_and_ingest.py             # CSV extraction and SQL generation script
    └── run_mysql_pipeline.py             # Automated CLI execution script for MySQL
```

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.10+**
* **MySQL Server 8.0+**

### Installation
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the complete project (starts MySQL instance and web dashboard):
   ```cmd
   run_project.bat
   ```

3. Open your browser at:
   ```text
   http://127.0.0.1:8000/
   ```

### Command-Line Execution
To execute all SQL scripts sequentially via the MySQL CLI:
```cmd
run_pipeline.bat
```
Or launch an interactive MySQL CLI session:
```cmd
open_mysql_cli.bat
```
