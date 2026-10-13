/* =====================================================================
   Supply Chain DBMS - Academic Project Portal Frontend Logic
   VIT Pune DBMS Project (Interactive CRUD & SQL Concepts)
   Target RDBMS: MySQL 8.0 on Port 3307
   ===================================================================== */

let allPorts = [];
let allCommodities = [];
let searchTimeout = null;

document.addEventListener("DOMContentLoaded", () => {
    fetchKpis();
    loadReferenceData();
    loadShipmentsTable();
    loadFilesSummary();
    runSyllabusQuery(1);
});

// ---------------------------------------------------------------------
// Tab Switcher
// ---------------------------------------------------------------------
function showTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-button").forEach(el => el.classList.remove("active"));

    const target = document.getElementById(tabId);
    if (target) target.classList.add("active");

    const tabBtnMap = {
        "tabCrud": "btnTabCrud",
        "tabFiles": "btnTabFiles",
        "tabTrigger": "btnTabTrigger",
        "tabProc": "btnTabProc",
        "tabQueries": "btnTabQueries"
    };
    const activeBtn = document.getElementById(tabBtnMap[tabId]);
    if (activeBtn) activeBtn.classList.add("active");

    if (tabId === "tabFiles") {
        loadFilesSummary();
    }
}

// ---------------------------------------------------------------------
// 1. KPI Statistics Fetcher (SQL Aggregate Functions)
// ---------------------------------------------------------------------
async function fetchKpis() {
    try {
        const res = await fetch("/api/stats");
        if (!res.ok) throw new Error("Stats request failed");
        const data = await res.json();

        const elTotal = document.getElementById("statTotalShipments");
        const elTransit = document.getElementById("statTransit");
        const elDisrupted = document.getElementById("statDisrupted");
        const elValue = document.getElementById("statValue");

        if (elTotal) elTotal.innerText = data.total_shipments ?? 0;
        if (elTransit) elTransit.innerText = (data.total_shipments - (data.disrupted_shipments || 0)) ?? 0;
        if (elDisrupted) elDisrupted.innerText = `${data.disrupted_shipments ?? 0} Ships`;

        const fmt = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
        if (elValue) elValue.innerText = fmt.format(data.total_value_usd ?? 0);
    } catch (err) {
        console.error("Failed to load KPIs:", err);
    }
}

// ---------------------------------------------------------------------
// 2. Load Reference Ports & Commodities for Dropdowns
// ---------------------------------------------------------------------
async function loadReferenceData() {
    try {
        const [portsRes, commRes] = await Promise.all([
            fetch("/api/ports?limit=250"),
            fetch("/api/commodities")
        ]);
        allPorts = await portsRes.json();
        allCommodities = await commRes.json();

        // Populate Add Modal Dropdowns
        const addOrig = document.getElementById("addOriginPort");
        const addDest = document.getElementById("addDestPort");
        const procPort = document.getElementById("selProcPort");

        if (addOrig) addOrig.innerHTML = "";
        if (addDest) addDest.innerHTML = "";
        if (procPort) procPort.innerHTML = '<option value="">-- Select a Disrupted Port --</option>';

        allPorts.forEach(p => {
            if (addOrig) {
                const opt1 = document.createElement("option");
                opt1.value = p.port_code;
                opt1.innerText = `${p.port_name} (${p.country_code})`;
                addOrig.appendChild(opt1);
            }

            if (addDest) {
                const opt2 = document.createElement("option");
                opt2.value = p.port_code;
                opt2.innerText = `${p.port_name} (${p.country_code})`;
                addDest.appendChild(opt2);
            }

            if (procPort) {
                const opt3 = document.createElement("option");
                opt3.value = p.port_code;
                opt3.innerText = `${p.port_name} (${p.country_code}) [${p.status}]`;
                procPort.appendChild(opt3);
            }
        });

        // Set default origin and destination
        if (addOrig && addOrig.options.length > 0) addOrig.selectedIndex = 0;
        if (addDest && addDest.options.length > 1) addDest.selectedIndex = 1;
        if (procPort && procPort.options.length > 1) procPort.selectedIndex = 1;

        // Populate Commodities
        const addComm = document.getElementById("addCommodity");
        if (addComm) {
            addComm.innerHTML = "";
            allCommodities.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c.commodity_id;
                opt.innerText = `${c.commodity_name} ($${c.avg_price_usd}/unit)`;
                addComm.appendChild(opt);
            });
        }

    } catch (err) {
        console.error("Error loading dropdown data:", err);
    }
}

// ---------------------------------------------------------------------
// 3. SHIPMENTS CRUD: SELECT with WHERE (LIKE, IN, BETWEEN)
// ---------------------------------------------------------------------
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadShipmentsTable();
    }, 250);
}

function resetFilters() {
    const elVessel = document.getElementById("fltVessel");
    const elStatus = document.getElementById("fltStatus");
    const elMinW = document.getElementById("fltMinWeight");
    const elMaxW = document.getElementById("fltMaxWeight");

    if (elVessel) elVessel.value = "";
    if (elStatus) elStatus.value = "all";
    if (elMinW) elMinW.value = "";
    if (elMaxW) elMaxW.value = "";

    loadShipmentsTable();
}

async function loadShipmentsTable() {
    const elVessel = document.getElementById("fltVessel");
    const elStatus = document.getElementById("fltStatus");
    const elMinW = document.getElementById("fltMinWeight");
    const elMaxW = document.getElementById("fltMaxWeight");

    const vessel = elVessel ? elVessel.value.trim() : "";
    const status = elStatus ? elStatus.value : "all";
    const minW = elMinW ? elMinW.value : "";
    const maxW = elMaxW ? elMaxW.value : "";

    let url = "/api/shipments?";
    if (vessel) url += `vessel_like=${encodeURIComponent(vessel)}&`;
    if (status && status !== "all") url += `status_filter=${encodeURIComponent(status)}&`;
    if (minW && maxW) url += `min_weight=${encodeURIComponent(minW)}&max_weight=${encodeURIComponent(maxW)}&`;

    const tbody = document.getElementById("tbodyShipments");
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="10" class="text-center">Querying MySQL database...</td></tr>';

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch shipments");
        const shipments = await res.json();

        const badge = document.getElementById("shipmentCountBadge");
        if (badge) badge.innerText = `${shipments.length} Record(s)`;

        tbody.innerHTML = "";

        if (shipments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center" style="padding: 24px;">No records match your WHERE filter criteria.</td></tr>';
            return;
        }

        const fmt = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

        shipments.forEach(s => {
            const tr = document.createElement("tr");

            let statusClass = "status-ok";
            if (s.status === "Disrupted") statusClass = "status-disrupted";
            else if (s.status === "Delivered") statusClass = "status-delivered";

            tr.innerHTML = `
                <td style="font-family: var(--font-code); color: var(--text-gray);">#${s.shipment_id}</td>
                <td style="font-family: var(--font-code); color: var(--color-primary); font-weight: 600;">${escapeHtml(s.tracking_number)}</td>
                <td><strong>${escapeHtml(s.vessel_name)}</strong></td>
                <td>${escapeHtml(s.origin_port_name)} &rarr; <strong>${escapeHtml(s.destination_port_name)}</strong></td>
                <td>${escapeHtml(s.commodity_name || 'General Cargo')}</td>
                <td style="font-family: var(--font-code);">${Number(s.cargo_weight_tonnes).toLocaleString()} MT</td>
                <td style="font-family: var(--font-code); font-weight: 600;">${fmt.format(s.estimated_value_usd)}</td>
                <td><span class="status-pill ${statusClass}">${escapeHtml(s.status)}</span></td>
                <td style="font-size: 0.78rem; color: #94a3b8; max-width: 180px; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(s.disruption_notes || '')}">${escapeHtml(s.disruption_notes || 'None')}</td>
                <td>
                    <button class="btn btn-sm btn-edit" onclick="openEditModal(${JSON.stringify(s).replace(/"/g, '&quot;')})">✏️ Edit</button>
                    <button class="btn btn-sm btn-delete" onclick="handleDeleteShipment(${s.shipment_id}, '${escapeHtml(s.tracking_number)}')">🗑️ Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="10" style="color: #ef4444;" class="text-center">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// ---------------------------------------------------------------------
// 4. SHIPMENTS DML: INSERT
// ---------------------------------------------------------------------
function openAddModal() {
    const elTrack = document.getElementById("addTracking");
    if (elTrack) elTrack.value = `SHP-2024-${Math.floor(1000 + Math.random() * 9000)}`;

    const modal = document.getElementById("modalAddShipment");
    if (modal) modal.style.display = "flex";
}

function closeAddModal() {
    const modal = document.getElementById("modalAddShipment");
    if (modal) modal.style.display = "none";
}

async function handleAddShipmentSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitAdd");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Inserting into MySQL...";
    }

    const payload = {
        tracking_number: document.getElementById("addTracking").value.trim(),
        vessel_name: document.getElementById("addVessel").value.trim(),
        origin_port_id: parseInt(document.getElementById("addOriginPort").value),
        destination_port_id: parseInt(document.getElementById("addDestPort").value),
        commodity_id: parseInt(document.getElementById("addCommodity").value),
        cargo_weight_tonnes: parseFloat(document.getElementById("addWeight").value),
        estimated_value_usd: parseFloat(document.getElementById("addValue").value),
        status: document.getElementById("addStatus").value,
        disruption_notes: document.getElementById("addNotes").value.trim()
    };

    try {
        const res = await fetch("/api/shipments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Insert failed");

        alert("✅ Success: " + result.message);
        closeAddModal();
        await fetchKpis();
        await loadShipmentsTable();
        await loadFilesSummary();
    } catch (err) {
        alert("❌ Error inserting shipment: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Save to Database (INSERT)";
        }
    }
}

// ---------------------------------------------------------------------
// 5. SHIPMENTS DML: UPDATE
// ---------------------------------------------------------------------
function openEditModal(s) {
    const elId = document.getElementById("editShipmentId");
    const elTrack = document.getElementById("editTracking");
    const elVessel = document.getElementById("editVessel");
    const elStatus = document.getElementById("editStatus");
    const elValue = document.getElementById("editValue");
    const elNotes = document.getElementById("editNotes");

    if (elId) elId.value = s.shipment_id;
    if (elTrack) elTrack.value = s.tracking_number;
    if (elVessel) elVessel.value = s.vessel_name;
    if (elStatus) elStatus.value = s.status;
    if (elValue) elValue.value = s.estimated_value_usd;
    if (elNotes) elNotes.value = s.disruption_notes || "";

    const modal = document.getElementById("modalEditShipment");
    if (modal) modal.style.display = "flex";
}

function closeEditModal() {
    const modal = document.getElementById("modalEditShipment");
    if (modal) modal.style.display = "none";
}

async function handleEditShipmentSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitEdit");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Updating in MySQL...";
    }

    const shipmentId = document.getElementById("editShipmentId").value;
    const payload = {
        vessel_name: document.getElementById("editVessel").value.trim(),
        status: document.getElementById("editStatus").value,
        estimated_value_usd: parseFloat(document.getElementById("editValue").value),
        disruption_notes: document.getElementById("editNotes").value.trim()
    };

    try {
        const res = await fetch(`/api/shipments/${shipmentId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Update failed");

        alert("✅ Success: " + result.message);
        closeEditModal();
        await fetchKpis();
        await loadShipmentsTable();
    } catch (err) {
        alert("❌ Error updating shipment: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Update Database (UPDATE)";
        }
    }
}

// ---------------------------------------------------------------------
// 6. SHIPMENTS DML: DELETE
// ---------------------------------------------------------------------
async function handleDeleteShipment(shipmentId, trackingNum) {
    if (!confirm(`Are you sure you want to delete shipment #${trackingNum}?\n\nThis will execute in MySQL:\nDELETE FROM SHIPMENTS WHERE shipment_id = ${shipmentId};`)) {
        return;
    }

    try {
        const res = await fetch(`/api/shipments/${shipmentId}`, { method: "DELETE" });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Delete failed");

        alert("✅ " + result.message);
        await fetchKpis();
        await loadShipmentsTable();
        await loadFilesSummary();
    } catch (err) {
        alert("❌ Error deleting shipment: " + err.message);
    }
}

// ---------------------------------------------------------------------
// 7. TAB 2: DATA FILES & TABLES SUMMARY
// ---------------------------------------------------------------------
async function loadFilesSummary() {
    const tbody = document.getElementById("tbodyFilesTable");
    if (!tbody) return;

    try {
        const res = await fetch("/api/tables-summary");
        if (!res.ok) throw new Error("Could not load tables summary");
        const data = await res.json();

        tbody.innerHTML = "";
        data.tables.forEach(t => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong style="color: var(--color-primary); font-family: var(--font-code);">${escapeHtml(t.table)}</strong></td>
                <td><code style="color: #cbd5e1;">${escapeHtml(t.source_csv)}</code></td>
                <td><strong style="font-family: var(--font-code); color: #10b981;">${Number(t.rows).toLocaleString()} rows</strong></td>
                <td><span class="status-pill status-ok">${escapeHtml(t.status)}</span></td>
                <td style="font-size: 0.82rem; color: #94a3b8;">${escapeHtml(t.description)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="color: #ef4444;" class="text-center">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// ---------------------------------------------------------------------
// 8. TRIGGER DEMO (Simulate Disaster & trg_after_disaster_insert)
// ---------------------------------------------------------------------
function setPreset(eventType, lat, lon, radius, desc) {
    const elEvent = document.getElementById("trigEvent");
    const elLat = document.getElementById("trigLat");
    const elLon = document.getElementById("trigLon");
    const elRadius = document.getElementById("trigRadius");
    const elDesc = document.getElementById("trigDesc");

    if (elEvent) elEvent.value = eventType;
    if (elLat) elLat.value = lat;
    if (elLon) elLon.value = lon;
    if (elRadius) elRadius.value = radius;
    if (elDesc) elDesc.value = desc;
}

async function handleTriggerSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btnFireTrigger");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "⏳ Executing Trigger in MySQL...";
    }

    const payload = {
        event_type: document.getElementById("trigEvent").value,
        severity_level: 4,
        alert_level: "Red",
        country: "Maritime Hazard Sector",
        latitude: parseFloat(document.getElementById("trigLat").value),
        longitude: parseFloat(document.getElementById("trigLon").value),
        radius_km: parseFloat(document.getElementById("trigRadius").value),
        description: document.getElementById("trigDesc").value
    };

    try {
        const res = await fetch("/api/simulate-disaster", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Trigger simulation failed");

        const box = document.getElementById("triggerResultBox");
        if (box) box.style.display = "block";

        const msgEl = document.getElementById("triggerMsg");
        if (msgEl) {
            msgEl.innerHTML = `
                <strong>${escapeHtml(data.message)}</strong> (Disaster ID: #${data.disaster_id})<br>
                Disaster epicenter at (${payload.latitude}, ${payload.longitude}) within impact radius of ${payload.radius_km} km.
            `;
        }

        let listHtml = `<p style="margin-top: 8px;"><strong>Ports in Hazard Danger Zone (${data.total_affected_ports} detected):</strong></p><ul style="margin-left: 20px; font-size: 0.85rem;">`;
        data.affected_ports.forEach(p => {
            listHtml += `<li><strong>${escapeHtml(p.port_name)}</strong> (${escapeHtml(p.country_code)}) &bull; ${p.distance_km} km away &rarr; Status updated to <code>Hazard Alert</code></li>`;
        });
        listHtml += `</ul>`;

        if (data.disrupted_shipments && data.disrupted_shipments.length > 0) {
            listHtml += `<p style="margin-top: 10px;"><strong>Shipments Automatically Marked Disrupted by Trigger:</strong></p><ul style="margin-left: 20px; font-size: 0.85rem; color: #ef4444;">`;
            data.disrupted_shipments.forEach(s => {
                listHtml += `<li>Vessel: <strong>${escapeHtml(s.vessel_name)}</strong> (${escapeHtml(s.tracking_number)}) &rarr; Status: <code>${escapeHtml(s.status)}</code></li>`;
            });
            listHtml += `</ul>`;
        }

        const affEl = document.getElementById("triggerAffectedList");
        if (affEl) affEl.innerHTML = listHtml;

        // Refresh KPIs, Shipments table, and Reference dropdowns
        await fetchKpis();
        await loadShipmentsTable();
        await loadReferenceData();
        await loadFilesSummary();

    } catch (err) {
        alert("❌ Error: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "🚀 Insert Disaster & Fire Trigger (DML INSERT)";
        }
    }
}

// ---------------------------------------------------------------------
// 9. STORED PROCEDURE DEMO (CALL sp_find_alternative_port)
// ---------------------------------------------------------------------
async function handleProcedureRun() {
    const elPort = document.getElementById("selProcPort");
    const elRadius = document.getElementById("selProcRadius");

    const portCode = elPort ? elPort.value : "";
    const radius = elRadius ? elRadius.value : "1000";

    if (!portCode) {
        alert("Please select a target disrupted port from the dropdown.");
        return;
    }

    try {
        const res = await fetch(`/api/find-alternative-port?port_code=${portCode}&radius_km=${radius}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Procedure call failed");

        const box = document.getElementById("procResultBox");
        if (box) box.style.display = "block";

        const tbody = document.getElementById("tbodyProcedure");
        if (!tbody) return;

        tbody.innerHTML = "";

        if (!data.alternatives || data.alternatives.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No safe alternative operational ports within this search radius.</td></tr>';
            return;
        }

        data.alternatives.forEach(alt => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong style="color: #10b981;">${escapeHtml(alt.port_name)}</strong></td>
                <td>${escapeHtml(alt.country_code)}</td>
                <td>${escapeHtml(alt.harbor_size)}</td>
                <td><strong>${alt.distance_from_disrupted_km} km</strong></td>
                <td><span class="status-pill status-delivered">Safe Candidate</span></td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        alert("Error executing stored procedure: " + err.message);
    }
}

// ---------------------------------------------------------------------
// 10. SQL SYLLABUS DEMONSTRATOR
// ---------------------------------------------------------------------
async function runSyllabusQuery(queryId) {
    document.querySelectorAll(".query-selector .btn").forEach(b => b.classList.remove("active"));
    const btn = document.getElementById(`qBtn${queryId}`);
    if (btn) btn.classList.add("active");

    const titleEl = document.getElementById("qTitle");
    const timerEl = document.getElementById("qTimer");
    const codeEl = document.getElementById("qCode");
    const thead = document.getElementById("theadQuery");
    const tbody = document.getElementById("tbodyQuery");

    if (codeEl) codeEl.innerText = "-- Loading query from MySQL 8.0...";
    if (thead) thead.innerHTML = "";
    if (tbody) tbody.innerHTML = '<tr><td class="text-center">Executing query...</td></tr>';

    try {
        const res = await fetch(`/api/run-query/${queryId}`);
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Query execution failed");

        if (titleEl) titleEl.innerText = `${result.title} (${result.concept})`;
        if (timerEl) timerEl.innerText = `Executed in ${result.execution_time_ms} ms (${result.total_rows} rows)`;
        if (codeEl) codeEl.innerText = result.sql;

        // Table Header
        if (thead && result.columns) {
            let thHtml = "<tr>";
            result.columns.forEach(c => {
                thHtml += `<th>${escapeHtml(c.replace(/_/g, ' ').toUpperCase())}</th>`;
            });
            thHtml += "</tr>";
            thead.innerHTML = thHtml;
        }

        // Table Body
        if (tbody && result.data) {
            let tbHtml = "";
            result.data.forEach(row => {
                tbHtml += "<tr>";
                result.columns.forEach(c => {
                    let v = row[c];
                    if (typeof v === "number" && c.includes("value")) {
                        v = "$" + v.toLocaleString();
                    }
                    tbHtml += `<td>${v !== null && v !== undefined ? escapeHtml(v) : ''}</td>`;
                });
                tbHtml += "</tr>";
            });
            tbody.innerHTML = tbHtml;
        }

    } catch (err) {
        if (tbody) tbody.innerHTML = `<tr><td style="color: #ef4444;">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
