import csv
import os
import random
from datetime import datetime, timedelta

BASE_DIR = r"e:\DBMS"
SQL_DIR = os.path.join(BASE_DIR, "sql")
os.makedirs(SQL_DIR, exist_ok=True)
OUTPUT_SQL = os.path.join(SQL_DIR, "02_sample_data.sql")

def escape_str(s):
    if s is None:
        return "NULL"
    s = str(s).replace("'", "''").strip()
    return f"'{s}'"

def parse_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default

def parse_int(v, default=0):
    try:
        return int(float(v))
    except:
        return default

print("Reading CSV datasets...")

# 1. PORTS
ports_file = os.path.join(BASE_DIR, "UpdatedPub150.csv")
ports = []
seen_ports = set()
with open(ports_file, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            port_code = int(row["port_code"])
            if port_code in seen_ports:
                continue
            seen_ports.add(port_code)
            lat = parse_float(row["latitude"])
            lon = parse_float(row["longitude"])
            if lat == 0.0 and lon == 0.0:
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            ports.append({
                "port_code": port_code,
                "port_name": row["port_name"].strip() or f"Port {port_code}",
                "country_code": row["country_code"].strip() or "Unknown",
                "un_locode": row.get("un_locode", "").strip() or None,
                "region_name": row.get("region_name", "").strip() or None,
                "harbor_size": row.get("harbor_size", "Medium").strip() or "Medium",
                "harbor_type": row.get("harbor_type", "Coastal (Natural)").strip() or "Coastal (Natural)",
                "lat": lat,
                "lon": lon
            })
        except Exception:
            continue

# Select top 250 diverse ports
sample_ports = ports[:250]
print(f"Loaded {len(sample_ports)} ports for MVP sample.")

# 2. COMMODITIES
commodities_file = os.path.join(BASE_DIR, "all_commodities_merged.csv")
commodities = []
seen_comm = set()
with open(commodities_file, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row["commodity_name"].strip()
        year = parse_int(row.get("year", 2024))
        key = (name, year)
        if key in seen_comm:
            continue
        seen_comm.add(key)
        commodities.append({
            "name": name,
            "year": year,
            "avg_price": parse_float(row.get("avg_price_usd", 100.0)),
            "annual_change": parse_float(row.get("annual_change_pct", 0.0))
        })
sample_commodities = commodities[:35]
print(f"Loaded {len(sample_commodities)} commodities.")

# 3. CONFLICTS
conflicts_file = os.path.join(BASE_DIR, "geopolitical_conflict_risk_dataset.csv")
conflicts = []
with open(conflicts_file, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        conflicts.append({
            "country": row["country"].strip(),
            "region": row.get("region", "").strip(),
            "recorded_month": row.get("recorded_month", "2024-01-01").strip(),
            "instability_score": parse_float(row.get("instability_score", 50.0)),
            "political_stability_index": parse_float(row.get("political_stability_index", 0.0)),
            "sanctions_active": parse_int(row.get("sanctions_active", 0)),
            "protest_events": parse_int(row.get("protest_events_last_3m", 0)),
            "conflict_escalation": parse_int(row.get("conflict_escalation_6m", 0)),
            "regime_type": row.get("regime_type", "Democracy").strip()
        })
sample_conflicts = conflicts[:120]
print(f"Loaded {len(sample_conflicts)} conflict records.")

# 4. DISASTERS
disasters_file = os.path.join(BASE_DIR, "all_disasters_merged.csv")
disasters = []
with open(disasters_file, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        lat = parse_float(row.get("latitude"))
        lon = parse_float(row.get("longitude"))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        if lat == 0.0 and lon == 0.0:
            continue
        
        event_type = row.get("event_type", "Hazard").strip()
        alert = row.get("alertlevel", "Orange").strip()
        severity = parse_int(row.get("severity_level", 2))
        
        # Determine radius
        radius = 250.0
        if "cyclone" in event_type.lower() or "hurricane" in event_type.lower():
            radius = 450.0
        elif "drought" in event_type.lower():
            radius = 350.0
        elif "flood" in event_type.lower():
            radius = 200.0
        elif "earthquake" in event_type.lower():
            radius = 180.0
            
        disasters.append({
            "event_type": event_type,
            "severity_level": severity,
            "alert_level": alert,
            "start_time": row.get("start_time", "2024-01-01 00:00:00").strip(),
            "end_time": row.get("end_time", "2024-01-10 00:00:00").strip(),
            "country": row.get("country", "International Waters").strip(),
            "iso3": row.get("iso3", "").strip(),
            "lat": lat,
            "lon": lon,
            "radius_km": radius,
            "description": row.get("description", f"{event_type} event").strip()
        })
sample_disasters = disasters[:100]
print(f"Loaded {len(sample_disasters)} disasters.")

# 5. SYNTHETIC REALISTIC SHIPMENTS
# Select pairs of sample ports
shipments = []
vessels = [
    "Ever Golden", "Maersk Mc-Kinney Moller", "CMA CGM Jacques Saade",
    "MSC Oscar", "HMM Algeciras", "Cosco Shipping Universe", "OOCL Hong Kong",
    "ONE Apus", "Yang Ming Wellhead", "Pacific Voyager", "Atlantic Pioneer",
    "Nordic Star", "Global Trader", "Orient Express", "Aegean Horizon",
    "Southern Cross", "Maritime Serenity", "Titan Express", "Ocean Monarch",
    "Starlight Carrier", "Baltic Wind", "Cape Horn Courier", "Arabian Crown",
    "Strait Navigator", "Antarctic Explorer"
]

random.seed(42)
start_dt = datetime(2024, 6, 1)

for idx, vessel in enumerate(vessels, start=1):
    orig = sample_ports[(idx * 7) % len(sample_ports)]
    dest = sample_ports[(idx * 13 + 5) % len(sample_ports)]
    if orig["port_code"] == dest["port_code"]:
        dest = sample_ports[(idx * 13 + 6) % len(sample_ports)]
        
    dep_date = start_dt + timedelta(days=random.randint(1, 20))
    arr_date = dep_date + timedelta(days=random.randint(10, 35))
    comm_idx = (idx % len(sample_commodities)) + 1
    weight = round(random.uniform(5000, 85000), 2)
    val = round(weight * random.uniform(80, 1200), 2)
    
    shipments.append({
        "tracking_num": f"SHP-2024-{idx:04d}",
        "vessel_name": vessel,
        "orig_id": orig["port_code"],
        "dest_id": dest["port_code"],
        "comm_id": comm_idx,
        "weight": weight,
        "value": val,
        "dep_date": dep_date.strftime("%Y-%m-%d %H:%M:%S"),
        "arr_date": arr_date.strftime("%Y-%m-%d %H:%M:%S")
    })

print(f"Generated {len(shipments)} realistic active shipments.")

# Write SQL script
print(f"Writing {OUTPUT_SQL}...")
with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
    f.write("-- =====================================================================\n")
    f.write("-- Global Supply Chain Disruption Predictor - MVP Sample Ingestion\n")
    f.write("-- Generated from CSV datasets\n")
    f.write("-- =====================================================================\n\n")
    f.write("USE supply_chain_db;\n\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
    f.write("TRUNCATE TABLE PORTS;\n")
    f.write("TRUNCATE TABLE COMMODITIES;\n")
    f.write("TRUNCATE TABLE CONFLICTS;\n")
    f.write("TRUNCATE TABLE DISASTERS;\n")
    f.write("TRUNCATE TABLE SHIPMENTS;\n")
    f.write("TRUNCATE TABLE DISRUPTION_LOG;\n")
    f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")

    # Ingest Ports
    f.write("-- Ingest Ports (using POINT(lat, lon) with SRID 4326)\n")
    f.write("INSERT INTO PORTS (port_code, port_name, country_code, un_locode, region_name, harbor_size, harbor_type, latitude, longitude, location, status) VALUES\n")
    port_vals = []
    for p in sample_ports:
        loc_str = f"ST_GeomFromText('POINT({p['lat']} {p['lon']})', 4326)"
        val = f"({p['port_code']}, {escape_str(p['port_name'])}, {escape_str(p['country_code'])}, {escape_str(p['un_locode'])}, {escape_str(p['region_name'])}, {escape_str(p['harbor_size'])}, {escape_str(p['harbor_type'])}, {p['lat']}, {p['lon']}, {loc_str}, 'Operational')"
        port_vals.append(val)
    f.write(",\n".join(port_vals) + ";\n\n")

    # Ingest Commodities
    f.write("-- Ingest Commodities\n")
    f.write("INSERT INTO COMMODITIES (commodity_name, year, avg_price_usd, annual_change_pct) VALUES\n")
    comm_vals = []
    for c in sample_commodities:
        comm_vals.append(f"({escape_str(c['name'])}, {c['year']}, {c['avg_price']}, {c['annual_change']})")
    f.write(",\n".join(comm_vals) + ";\n\n")

    # Ingest Conflicts
    f.write("-- Ingest Geopolitical Conflict Risks\n")
    f.write("INSERT INTO CONFLICTS (country, region, recorded_month, instability_score, political_stability_index, sanctions_active, protest_events_last_3m, conflict_escalation_6m, regime_type) VALUES\n")
    conf_vals = []
    for cf in sample_conflicts:
        conf_vals.append(f"({escape_str(cf['country'])}, {escape_str(cf['region'])}, {escape_str(cf['recorded_month'])}, {cf['instability_score']}, {cf['political_stability_index']}, {cf['sanctions_active']}, {cf['protest_events']}, {cf['conflict_escalation']}, {escape_str(cf['regime_type'])})")
    f.write(",\n".join(conf_vals) + ";\n\n")

    # Ingest Disasters
    f.write("-- Ingest Disasters (Disaster inserts fire trg_after_disaster_insert)\n")
    f.write("INSERT INTO DISASTERS (event_type, severity_level, alert_level, start_time, end_time, country, iso3, latitude, longitude, location, radius_km, description) VALUES\n")
    dis_vals = []
    for d in sample_disasters:
        loc_str = f"ST_GeomFromText('POINT({d['lat']} {d['lon']})', 4326)"
        val = f"({escape_str(d['event_type'])}, {d['severity_level']}, {escape_str(d['alert_level'])}, {escape_str(d['start_time'])}, {escape_str(d['end_time'])}, {escape_str(d['country'])}, {escape_str(d['iso3'])}, {d['lat']}, {d['lon']}, {loc_str}, {d['radius_km']}, {escape_str(d['description'])})"
        dis_vals.append(val)
    f.write(",\n".join(dis_vals) + ";\n\n")

    # Ingest Shipments
    f.write("-- Ingest Active Baseline Shipments\n")
    f.write("INSERT INTO SHIPMENTS (tracking_number, vessel_name, origin_port_id, destination_port_id, commodity_id, cargo_weight_tonnes, estimated_value_usd, departure_date, estimated_arrival, status, risk_level, disruption_notes) VALUES\n")
    shp_vals = []
    for s in shipments:
        val = f"({escape_str(s['tracking_num'])}, {escape_str(s['vessel_name'])}, {s['orig_id']}, {s['dest_id']}, {s['comm_id']}, {s['weight']}, {s['value']}, {escape_str(s['dep_date'])}, {escape_str(s['arr_date'])}, 'In Transit', 'Low', 'Baseline Transit')"
        shp_vals.append(val)
    f.write(",\n".join(shp_vals) + ";\n\n")

    # Synchronize initial disruption statuses for any shipments whose ports are near disasters
    f.write("-- Synchronize initial disruption statuses via Spatial Distance calculation\n")
    f.write("""
UPDATE PORTS p
INNER JOIN DISASTERS d ON ST_Distance_Sphere(p.location, d.location) <= (d.radius_km * 1000)
SET p.status = 'Hazard Alert';

UPDATE SHIPMENTS s
INNER JOIN PORTS p ON s.destination_port_id = p.port_code OR s.origin_port_id = p.port_code
INNER JOIN DISASTERS d ON ST_Distance_Sphere(p.location, d.location) <= (d.radius_km * 1000)
SET s.status = 'Disrupted',
    s.risk_level = 'Critical',
    s.disruption_notes = CONCAT('Hazard Alert: Near ', d.event_type, ' (', d.alert_level, ') within ', ROUND(d.radius_km), 'km');
""")

print("Successfully generated 02_sample_data.sql.")
