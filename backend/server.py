import os
import pymysql
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "supply_chain_db",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True
}

def get_db():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

app = FastAPI(title="Global Supply Chain Disruption Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

class DisasterSimulation(BaseModel):
    event_type: str
    severity_level: int = 3
    alert_level: str = "Orange"
    country: str = "International Waters"
    latitude: float
    longitude: float
    radius_km: float = 300.0
    description: str

class ShipmentCreate(BaseModel):
    tracking_number: str
    vessel_name: str
    origin_port_id: int
    destination_port_id: int
    commodity_id: int = 1
    cargo_weight_tonnes: float = 25000.0
    estimated_value_usd: float = 1500000.0
    departure_date: str = "2024-06-01 00:00:00"
    estimated_arrival: str = "2024-06-25 00:00:00"
    status: str = "In Transit"
    risk_level: str = "Low"
    disruption_notes: str = "Scheduled transit"

class ShipmentUpdate(BaseModel):
    vessel_name: Optional[str] = None
    status: Optional[str] = None
    estimated_value_usd: Optional[float] = None
    disruption_notes: Optional[str] = None

@app.get("/api/health")
def health_check():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS version, DATABASE() AS db;")
        info = cur.fetchone()
    conn.close()
    return {"status": "online", "database": info}

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    stats = {}
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'Hazard Alert' THEN 1 ELSE 0 END) AS hazard_ports FROM PORTS;")
        p_row = cur.fetchone()
        stats["total_ports"] = p_row["total"]
        stats["hazard_ports"] = p_row["hazard_ports"] or 0

        cur.execute("""
            SELECT 
                COUNT(*) AS total_shipments,
                SUM(CASE WHEN status = 'Disrupted' THEN 1 ELSE 0 END) AS disrupted_shipments,
                SUM(CASE WHEN status = 'Disrupted' THEN estimated_value_usd ELSE 0 END) AS disrupted_value_usd,
                SUM(estimated_value_usd) AS total_value_usd
            FROM SHIPMENTS;
        """)
        s_row = cur.fetchone()
        stats["total_shipments"] = s_row["total_shipments"]
        stats["disrupted_shipments"] = s_row["disrupted_shipments"] or 0
        stats["disrupted_value_usd"] = float(s_row["disrupted_value_usd"] or 0)
        stats["total_value_usd"] = float(s_row["total_value_usd"] or 0)

        cur.execute("SELECT COUNT(*) AS total_disasters FROM DISASTERS;")
        stats["total_disasters"] = cur.fetchone()["total_disasters"]

        cur.execute("SELECT COUNT(*) AS high_conflict_countries FROM CONFLICTS WHERE sanctions_active = 1 OR instability_score >= 70.0;")
        stats["high_conflict_countries"] = cur.fetchone()["high_conflict_countries"]

    conn.close()
    return stats

@app.get("/api/tables-summary")
def get_tables_summary():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM PORTS;")
        ports_cnt = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM COMMODITIES;")
        comm_cnt = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM CONFLICTS;")
        conf_cnt = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM DISASTERS;")
        dis_cnt = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM SHIPMENTS;")
        shp_cnt = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM DISRUPTION_LOG;")
        log_cnt = cur.fetchone()["c"]
    conn.close()
    return {
        "tables": [
            {"table": "PORTS", "source_csv": "UpdatedPub150.csv", "rows": ports_cnt, "status": "Loaded (MySQL Spatial POINT 4326)", "description": "Global ports with spatial locations, harbor sizes & status"},
            {"table": "COMMODITIES", "source_csv": "all_commodities_merged.csv", "rows": comm_cnt, "status": "Loaded", "description": "Global maritime commodities, historical unit pricing & annual change"},
            {"table": "CONFLICTS", "source_csv": "geopolitical_conflict_risk_dataset.csv", "rows": conf_cnt, "status": "Loaded", "description": "Country instability scores, sanctions indicators & conflict escalations"},
            {"table": "DISASTERS", "source_csv": "all_disasters_merged.csv", "rows": dis_cnt, "status": "Loaded (MySQL Spatial POINT 4326)", "description": "Cyclones, earthquakes, droughts with danger radius & alert levels"},
            {"table": "SHIPMENTS", "source_csv": "Interactive DML Operational Table", "rows": shp_cnt, "status": "Active (Live CRUD)", "description": "Vessel voyages, cargo values, route ports & disruption statuses"},
            {"table": "DISRUPTION_LOG", "source_csv": "MySQL Trigger Audit Log", "rows": log_cnt, "status": "Automated", "description": "Security audit records auto-generated by trg_after_disaster_insert"}
        ]
    }

@app.get("/api/ports")
def get_ports(limit: int = 300):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                port_code, port_name, country_code, un_locode, region_name, 
                harbor_size, harbor_type, latitude, longitude, status
            FROM PORTS
            LIMIT %s;
        """, (limit,))
        ports = cur.fetchall()
    conn.close()
    return ports

@app.get("/api/disasters")
def get_disasters(limit: int = 150):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                disaster_id, event_type, severity_level, alert_level, 
                country, latitude, longitude, radius_km, description, start_time
            FROM DISASTERS
            ORDER BY disaster_id DESC
            LIMIT %s;
        """, (limit,))
        disasters = cur.fetchall()
    conn.close()
    return disasters

@app.get("/api/commodities")
def get_commodities():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT commodity_id, commodity_name, avg_price_usd FROM COMMODITIES ORDER BY commodity_name ASC;")
        commodities = cur.fetchall()
        for c in commodities:
            c["avg_price_usd"] = float(c["avg_price_usd"])
    conn.close()
    return commodities

@app.get("/api/shipments")
def get_shipments(
    vessel_like: Optional[str] = None,
    status_filter: Optional[str] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None
):
    conn = get_db()
    query = """
        SELECT 
            s.shipment_id, s.tracking_number, s.vessel_name,
            s.origin_port_id, op.port_name AS origin_port_name, op.country_code AS origin_country,
            s.destination_port_id, dp.port_name AS destination_port_name, dp.country_code AS destination_country,
            s.commodity_id, c.commodity_name,
            s.cargo_weight_tonnes, s.estimated_value_usd,
            s.departure_date, s.estimated_arrival, s.status, s.risk_level, s.disruption_notes
        FROM SHIPMENTS s
        INNER JOIN PORTS op ON s.origin_port_id = op.port_code
        INNER JOIN PORTS dp ON s.destination_port_id = dp.port_code
        LEFT JOIN COMMODITIES c ON s.commodity_id = c.commodity_id
        WHERE 1=1
    """
    params = []
    if vessel_like:
        query += " AND s.vessel_name LIKE %s"
        params.append(f"%{vessel_like}%")
    if status_filter and status_filter != "all":
        query += " AND s.status = %s"
        params.append(status_filter)
    if min_weight is not None and max_weight is not None:
        query += " AND s.cargo_weight_tonnes BETWEEN %s AND %s"
        params.extend([min_weight, max_weight])

    query += " ORDER BY s.shipment_id DESC;"

    with conn.cursor() as cur:
        cur.execute(query, tuple(params))
        shipments = cur.fetchall()
        for s in shipments:
            s["cargo_weight_tonnes"] = float(s["cargo_weight_tonnes"])
            s["estimated_value_usd"] = float(s["estimated_value_usd"])
    conn.close()
    return shipments

@app.post("/api/shipments")
def create_shipment(payload: ShipmentCreate):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO SHIPMENTS (
                    tracking_number, vessel_name, origin_port_id, destination_port_id,
                    commodity_id, cargo_weight_tonnes, estimated_value_usd,
                    departure_date, estimated_arrival, status, risk_level, disruption_notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cur.execute(sql, (
                payload.tracking_number,
                payload.vessel_name,
                payload.origin_port_id,
                payload.destination_port_id,
                payload.commodity_id,
                payload.cargo_weight_tonnes,
                payload.estimated_value_usd,
                payload.departure_date,
                payload.estimated_arrival,
                payload.status,
                payload.risk_level,
                payload.disruption_notes
            ))
            new_id = cur.lastrowid
        conn.close()
        return {"success": True, "shipment_id": new_id, "message": "Shipment record inserted successfully (DML INSERT)."}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/shipments/{shipment_id}")
def update_shipment(shipment_id: int, payload: ShipmentUpdate):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM SHIPMENTS WHERE shipment_id = %s;", (shipment_id,))
            exists = cur.fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Shipment not found")

            updates = []
            values = []
            if payload.vessel_name is not None:
                updates.append("vessel_name = %s")
                values.append(payload.vessel_name)
            if payload.status is not None:
                updates.append("status = %s")
                values.append(payload.status)
            if payload.estimated_value_usd is not None:
                updates.append("estimated_value_usd = %s")
                values.append(payload.estimated_value_usd)
            if payload.disruption_notes is not None:
                updates.append("disruption_notes = %s")
                values.append(payload.disruption_notes)

            if not updates:
                return {"success": True, "message": "No fields to update."}

            sql = f"UPDATE SHIPMENTS SET {', '.join(updates)} WHERE shipment_id = %s;"
            values.append(shipment_id)
            cur.execute(sql, tuple(values))

        conn.close()
        return {"success": True, "shipment_id": shipment_id, "message": "Shipment updated successfully in MySQL (DML UPDATE)."}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/shipments/{shipment_id}")
def delete_shipment(shipment_id: int):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM SHIPMENTS WHERE shipment_id = %s;", (shipment_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Shipment not found")
        conn.close()
        return {"success": True, "shipment_id": shipment_id, "message": "Shipment deleted successfully from MySQL (DML DELETE)."}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/disrupted-shipments")
def get_disrupted_shipments():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM v_disrupted_shipments;")
        disrupted = cur.fetchall()
        for row in disrupted:
            row["cargo_weight_tonnes"] = float(row["cargo_weight_tonnes"])
            row["estimated_value_usd"] = float(row["estimated_value_usd"])
    conn.close()
    return disrupted

@app.get("/api/conflicts")
def get_conflicts(limit: int = 50):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT country, region, instability_score, political_stability_index, sanctions_active, conflict_escalation_6m, regime_type
            FROM CONFLICTS
            ORDER BY instability_score DESC
            LIMIT %s;
        """, (limit,))
        conflicts = cur.fetchall()
        for c in conflicts:
            c["instability_score"] = float(c["instability_score"])
            c["political_stability_index"] = float(c["political_stability_index"])
    conn.close()
    return conflicts

@app.post("/api/simulate-disaster")
def simulate_disaster(payload: DisasterSimulation):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO DISASTERS 
                (event_type, severity_level, alert_level, start_time, country, latitude, longitude, location, radius_km, description)
                VALUES 
                (%s, %s, %s, NOW(), %s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s);
            """
            loc_str = f"POINT({payload.latitude} {payload.longitude})"
            cur.execute(sql, (
                payload.event_type,
                payload.severity_level,
                payload.alert_level,
                payload.country,
                payload.latitude,
                payload.longitude,
                loc_str,
                payload.radius_km,
                payload.description
            ))
            disaster_id = cur.lastrowid

            # Fetch what was affected by the trigger execution
            cur.execute("""
                SELECT p.port_code, p.port_name, p.country_code,
                       ROUND(ST_Distance_Sphere(p.location, ST_GeomFromText(%s, 4326)) / 1000, 2) AS distance_km
                FROM PORTS p
                WHERE ST_Distance_Sphere(p.location, ST_GeomFromText(%s, 4326)) <= (%s * 1000);
            """, (loc_str, loc_str, payload.radius_km))
            affected_ports = cur.fetchall()

            cur.execute("""
                SELECT s.tracking_number, s.vessel_name, s.status, s.risk_level, s.disruption_notes
                FROM SHIPMENTS s
                WHERE s.status = 'Disrupted';
            """)
            disrupted_shipments = cur.fetchall()

            cur.execute("""
                SELECT * FROM DISRUPTION_LOG WHERE disaster_id = %s ORDER BY log_id DESC;
            """, (disaster_id,))
            trigger_logs = cur.fetchall()

        conn.close()
        return {
            "success": True,
            "disaster_id": disaster_id,
            "message": f"Disaster recorded successfully. MySQL trigger 'trg_after_disaster_insert' executed.",
            "affected_ports": affected_ports,
            "total_affected_ports": len(affected_ports),
            "disrupted_shipments": disrupted_shipments,
            "trigger_logs": trigger_logs
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/find-alternative-port")
def find_alternative_port(port_code: int = Query(...), radius_km: float = Query(1200.0)):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Query original port
            cur.execute("SELECT port_code, port_name, country_code, latitude, longitude, status FROM PORTS WHERE port_code = %s;", (port_code,))
            orig_port = cur.fetchone()
            if not orig_port:
                raise HTTPException(status_code=404, detail="Port not found")

            # Call stored procedure
            cur.execute("CALL sp_find_alternative_port(%s, %s);", (port_code, radius_km))
            alternatives = cur.fetchall()
            for alt in alternatives:
                alt["latitude"] = float(alt["latitude"])
                alt["longitude"] = float(alt["longitude"])
                alt["distance_from_disrupted_km"] = float(alt["distance_from_disrupted_km"])
                alt["political_risk_score"] = float(alt["political_risk_score"])

        conn.close()
        return {
            "original_port": orig_port,
            "search_radius_km": radius_km,
            "alternatives": alternatives
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/run-query/{query_id}")
def run_analytical_query(query_id: int):
    conn = get_db()
    queries = {
        1: {
            "title": "Query 1: Spatial Proximity & Pattern Matching",
            "concept": "Joins + Spatial ST_Distance_Sphere + LIKE / NOT LIKE + IS NOT NULL",
            "sql": """SELECT 
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
WHERE (p.port_name LIKE '%Port%' OR p.port_name LIKE '%Terminal%' OR p.port_name LIKE '%Bay%')
  AND p.harbor_type NOT LIKE '%River%'
  AND p.un_locode IS NOT NULL
ORDER BY distance_km ASC;"""
        },
        2: {
            "title": "Query 2: Multi-Aggregation & Exposure Grouping",
            "concept": "COUNT, SUM, AVG, MIN, MAX + GROUP BY + HAVING + BETWEEN...AND",
            "sql": """SELECT 
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
ORDER BY total_value_at_risk_usd DESC;"""
        },
        3: {
            "title": "Query 3: Advanced Subqueries (Nested & Correlated)",
            "concept": "Nested Subquery in WHERE + Correlated in SELECT + NOT IN + IS NOT NULL",
            "sql": """SELECT 
    s.tracking_number,
    s.vessel_name,
    dp.port_name AS destination_port,
    dp.country_code,
    s.estimated_value_usd,
    (
        SELECT cf.instability_score 
        FROM CONFLICTS cf 
        WHERE cf.country = dp.country_code 
        ORDER BY cf.recorded_month DESC 
        LIMIT 1
    ) AS country_instability_score
FROM SHIPMENTS s
INNER JOIN PORTS dp ON s.destination_port_id = dp.port_code
WHERE dp.country_code NOT IN ('Unknown', 'Disputed')
  AND s.disruption_notes IS NOT NULL
  AND dp.country_code IN (
      SELECT country 
      FROM CONFLICTS 
      WHERE instability_score > (
          SELECT AVG(instability_score) 
          FROM CONFLICTS
      )
  )
ORDER BY s.estimated_value_usd DESC;"""
        },
        4: {
            "title": "Query 4: Set Operator UNION",
            "concept": "UNION (Disaster Danger Zones + Sanctioned High-Conflict Zones)",
            "sql": """SELECT 
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

ORDER BY chokepoint_type, port_name;"""
        }
    }

    if query_id not in queries:
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid query ID (must be 1, 2, 3, or 4)")

    q_data = queries[query_id]
    try:
        with conn.cursor() as cur:
            import time
            start = time.time()
            cur.execute(q_data["sql"])
            rows = cur.fetchall()
            elapsed_ms = round((time.time() - start) * 1000, 2)
            
            formatted_rows = []
            for r in rows:
                new_r = {}
                for k, v in r.items():
                    if isinstance(v, (int, float, str, type(None))):
                        new_r[k] = v
                    else:
                        new_r[k] = str(v)
                formatted_rows.append(new_r)

        conn.close()
        return {
            "query_id": query_id,
            "title": q_data["title"],
            "concept": q_data["concept"],
            "sql": q_data["sql"],
            "execution_time_ms": elapsed_ms,
            "total_rows": len(formatted_rows),
            "columns": list(formatted_rows[0].keys()) if formatted_rows else [],
            "data": formatted_rows
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
