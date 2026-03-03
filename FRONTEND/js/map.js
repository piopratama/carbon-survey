const map = L.map("map").setView([-2, 118], 5);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
}).addTo(map);

let marker = null;
let aoiLayer = null;
let originalAOI = null;
let editHandler = null;
let projectAOILayer = null; // AOI dari project terpilih

let finalAOIGeometry = null;

let sentinelTrueColor = null;
let sentinelNDVI = null;
let sentinelControl = null;

let CURRENT_PROJECT_ID = null;
let projectMap = {}; // <-- WAJIB

let MANUAL_MODE_ACTIVE = false;

function isEditModeActive() {
    return !!editHandler;
}

function enableEditAOI() {
    if (!aoiLayer) return;

    if (!editHandler) {
        // MASUK MODE EDIT
        editHandler = new L.EditToolbar.Edit(map, { featureGroup: aoiLayer });
        editHandler.enable();

        editBtn.textContent = "Selesai Edit";
        statusEl.textContent = "Edit area aktif.";

        // disable save saat edit
        saveBtn.disabled = true;
    } else {
        // KELUAR MODE EDIT
        editHandler.disable();
        editHandler = null;

        editBtn.textContent = "Edit Area";
        statusEl.textContent = "Edit selesai.";

        // save aktif hanya kalau nama ada
        saveBtn.disabled = projectNameInput.value.trim() === "";
    }
}

function resetAOI() {
    if (!originalAOI) return;
    if (editHandler) enableEditAOI();

    map.removeLayer(aoiLayer);
    aoiLayer = L.geoJSON(originalAOI).addTo(map);
    statusEl.textContent = "Area direset.";
}

function confirmAOI() {
    const geo = aoiLayer.toGeoJSON();
    const feature = geo.features ? geo.features[0] : geo;
    finalAOIGeometry = feature.geometry;

    document.getElementById("sentinelSection").style.display = "block";
    document.getElementById("saveProjectBtn").disabled = false;

    statusEl.textContent = "Area dikunci. Silakan simpan project.";
}