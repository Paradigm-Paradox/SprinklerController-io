// GardenControl-io Frontend Controller

let activeRuns = [];
let allBeds = [];
let allCrops = [];

// Determine base API path (handles Home Assistant Ingress prefixes automatically)
const basePath = window.location.pathname.replace(/\/+$/, "");

async function apiFetch(endpoint, options = {}) {
    const url = `${basePath}${endpoint}`;
    const res = await fetch(url, options);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
    }
    return res.json();
}

async function refreshAll() {
    try {
        await Promise.all([
            fetchSystemStatus(),
            fetchBedsAndPlantings(),
            fetchZones(),
            fetchCrops()
        ]);
    } catch (e) {
        console.error("Refresh error:", e);
    }
}

async function fetchSystemStatus() {
    const data = await apiFetch("/api/system/status");
    document.getElementById("kpiEt0").textContent = `${data.daily_et0_mm} mm/day`;
    document.getElementById("kpiWaterToday").textContent = `${data.water_used_today_liters} L`;
    document.getElementById("kpiActiveZones").textContent = `${data.active_runs.length} Zones`;
    
    if (data.cistern_level_pct !== null) {
        document.getElementById("cisternBadge").textContent = `💧 Cistern: ${Math.round(data.cistern_level_pct)}%`;
    }
    if (data.solar_power_watts !== null) {
        document.getElementById("solarBadge").textContent = `☀️ Solar: ${Math.round(data.solar_power_watts)}W`;
    }

    activeRuns = data.active_runs || [];
    if (activeRuns.length > 0) {
        const first = activeRuns[0];
        document.getElementById("kpiCyclePhase").textContent = `Zone ${first.zone_id}: ${first.phase.toUpperCase()} (Pulse ${first.current_pulse}/${first.total_pulses})`;
    } else {
        document.getElementById("kpiCyclePhase").textContent = "All circuits idle";
    }
}

async function fetchBedsAndPlantings() {
    allBeds = await apiFetch("/api/beds");
    const container = document.getElementById("bedsList");
    container.innerHTML = "";

    for (const bed of allBeds) {
        const plantings = await apiFetch(`/api/beds/${bed.id}/plantings`);
        const card = document.createElement("div");
        card.className = "bed-card";
        card.innerHTML = `
            <div class="bed-header">
                <div>
                    <div class="bed-title">${bed.name}</div>
                    <div class="bed-specs">${bed.width_cm}x${bed.length_cm} cm • ${bed.soil_type.toUpperCase()} soil • Target ${bed.moisture_target_pct}% VWC</div>
                </div>
            </div>
            <div class="plantings-grid">
                ${plantings.length > 0 ? plantings.map(p => `
                    <div class="crop-chip">
                        <div class="crop-name">🌱 ${p.common_name} (x${p.quantity})</div>
                        <div class="crop-stage">Stage: ${p.current_stage}</div>
                        <div class="crop-harvest">${p.expected_harvest ? 'Harvest: ' + p.expected_harvest : 'Planted: ' + p.planted_at}</div>
                    </div>
                `).join('') : '<div class="text-muted" style="font-size: 0.85rem; padding: 4px;">No active crops in this bed yet.</div>'}
            </div>
        `;
        container.appendChild(card);
    }
}

async function fetchZones() {
    const zones = await apiFetch("/api/zones");
    const container = document.getElementById("zonesList");
    container.innerHTML = "";

    for (const zone of zones) {
        const activeRun = activeRuns.find(r => r.zone_id === zone.id);
        const isRunning = Boolean(activeRun);
        const phase = activeRun ? activeRun.phase : "idle";

        const card = document.createElement("div");
        card.className = "zone-card";
        card.innerHTML = `
            <div class="zone-header">
                <div>
                    <strong>${zone.name}</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8;">${zone.cycle_minutes}m cycle / ${zone.soak_minutes}m soak • ${zone.flow_rate_lpm} L/min</div>
                </div>
                <span class="zone-status-badge status-${phase}">${phase}</span>
            </div>
            ${isRunning ? `
                <div style="font-size: 0.8rem; margin: 8px 0; color: #38bdf8;">
                    Pulse ${activeRun.current_pulse} of ${activeRun.total_pulses} • Delivered: ${activeRun.estimated_liters} L
                </div>
            ` : ''}
            <div class="zone-controls">
                ${isRunning ? `
                    <button class="btn btn-sm btn-danger" onclick="stopZone('${zone.id}')">Stop Zone</button>
                ` : `
                    <button class="btn btn-sm btn-primary" onclick="triggerZone('${zone.id}', 16, true)">Start Cycle & Soak</button>
                    <button class="btn btn-sm btn-secondary" onclick="triggerZone('${zone.id}', 10, false)">Quick Run (10m)</button>
                `}
            </div>
        `;
        container.appendChild(card);
    }
}

async function fetchCrops() {
    allCrops = await apiFetch("/api/crops");
    const select = document.getElementById("cropSelect");
    if (select.children.length <= 1) {
        allCrops.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = `${c.common_name} (${c.category})`;
            select.appendChild(opt);
        });
    }
}

async function renderCompanionAdvice() {
    const cropId = document.getElementById("cropSelect").value;
    const box = document.getElementById("companionDetails");
    if (!cropId) {
        box.innerHTML = "";
        return;
    }

    const advice = await apiFetch(`/api/crops/${cropId}/companions`);
    box.innerHTML = `
        <div class="companion-good"><strong>Beneficial Companions:</strong> ${advice.beneficial_companions.join(', ') || 'None specified'}</div>
        <div class="companion-bad"><strong>Avoid Planting Near:</strong> ${advice.antagonist_plants.join(', ') || 'None reported'}</div>
    `;
}

async function triggerZone(zoneId, durationMinutes, cycleAndSoak) {
    try {
        await apiFetch(`/api/zones/${zoneId}/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                duration_minutes: durationMinutes,
                use_cycle_and_soak: cycleAndSoak
            })
        });
        await refreshAll();
    } catch (err) {
        alert("Irrigation trigger error: " + err.message);
    }
}

async function stopZone(zoneId) {
    try {
        await apiFetch(`/api/zones/${zoneId}/stop`, { method: "POST" });
        await refreshAll();
    } catch (err) {
        alert("Stop error: " + err.message);
    }
}

async function stopAllZones() {
    for (const r of activeRuns) {
        await stopZone(r.zone_id);
    }
}

function openPlantModal() {
    const bedSelect = document.getElementById("modalBedSelect");
    bedSelect.innerHTML = "";
    allBeds.forEach(b => {
        const opt = document.createElement("option");
        opt.value = b.id;
        opt.textContent = b.name;
        bedSelect.appendChild(opt);
    });

    const cropSelect = document.getElementById("modalCropSelect");
    cropSelect.innerHTML = "";
    allCrops.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.common_name;
        cropSelect.appendChild(opt);
    });

    document.getElementById("plantModal").classList.remove("hidden");
}

function closePlantModal() {
    document.getElementById("plantModal").classList.add("hidden");
}

async function submitPlanting() {
    const bedId = document.getElementById("modalBedSelect").value;
    const cropId = document.getElementById("modalCropSelect").value;
    const qty = parseInt(document.getElementById("modalQty").value, 10) || 1;
    const notes = document.getElementById("modalNotes").value;

    try {
        await apiFetch(`/api/beds/${bedId}/plantings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                crop_id: cropId,
                quantity: qty,
                notes: notes
            })
        });
        closePlantModal();
        await fetchBedsAndPlantings();
    } catch (err) {
        alert("Planting failed: " + err.message);
    }
}

// Initial boot & periodic poll
refreshAll();
setInterval(refreshAll, 4000);
