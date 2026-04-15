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

function handleImportAOI() {
    const file = document.getElementById("importFileInput").files[0];

    if (!file) {
        alert("Select file first");
        return;
    }

    const name = file.name.toLowerCase();

    if (name.endsWith(".kml")) {
        importKML(file);
    } else if (name.endsWith(".geojson") || name.endsWith(".json")) {
        importGeoJSON(file);
    } else {
        importCSV(file);
    }
}

function importKML(file) {
    const reader = new FileReader();

    reader.onload = function (e) {
        const layer = omnivore.kml.parse(e.target.result);

        // remove old AOI
        if (aoiLayer) {
            map.removeLayer(aoiLayer);
        }

        // use as AOI layer
        aoiLayer = layer.addTo(map);

        // zoom
        map.fitBounds(aoiLayer.getBounds());

        // extract coords (lng, lat)
        const coords = [];

        aoiLayer.eachLayer((l) => {
            if (l.getLatLngs) {
                const latlngs = L.LineUtil.isFlat(l.getLatLngs())
                    ? l.getLatLngs()
                    : l.getLatLngs()[0];

                latlngs.forEach((c) => {
                    coords.push([c.lng, c.lat]);
                });
            }
        });

        // convert to GeoJSON
        const geojson = {
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [coords]
            }
        };

        // save states
        originalAOI = geojson;
        finalAOIGeometry = geojson.geometry;

        // force NEW project
        CURRENT_PROJECT_ID = null;
        document.getElementById("projectSelect").value = "";

        // create center marker
        const center = aoiLayer.getBounds().getCenter();

        if (marker) {
            map.removeLayer(marker);
        }

        marker = L.marker(center).addTo(map);

        // UI update
        document.getElementById("aoiControlSection").style.display = "grid";
        editBtn.disabled = false;
        resetBtn.disabled = false;

        document.getElementById("status").innerText =
            "AOI imported. Masukkan nama project lalu simpan ✔";
    };

    reader.readAsText(file);
}

function importCSV(file) {
    const reader = new FileReader();

    reader.onload = function (e) {
        const lines = e.target.result.split("\n");

        const coords = lines
            .map((l) => l.split(","))
            .map(([lat, lng]) => [parseFloat(lat), parseFloat(lng)])
            .filter(([lat, lng]) => !isNaN(lat) && !isNaN(lng));

        if (coords.length < 3) {
            alert("Need at least 3 points");
            return;
        }

        if (window.importLayer) {
            map.removeLayer(window.importLayer);
        }

        // remove old AOI
        if (aoiLayer) {
            map.removeLayer(aoiLayer);
        }

        // convert to GeoJSON (lng, lat)
        const geojson = {
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [coords.map(c => [c[1], c[0]])]
            }
        };

        // create AOI layer (IMPORTANT)
        aoiLayer = L.geoJSON(geojson, {
            style: { color: "#0d6efd", weight: 2, fillOpacity: 0.1 },
        }).addTo(map);

        // zoom
        map.fitBounds(aoiLayer.getBounds());

        // save states (IMPORTANT)
        originalAOI = geojson;
        finalAOIGeometry = geojson.geometry;

        // UI update
        document.getElementById("aoiControlSection").style.display = "grid";
        editBtn.disabled = false;
        resetBtn.disabled = false;

        document.getElementById("status").innerText =
            "AOI imported from CSV ✔";

        enableSaveProject();
    };

    reader.readAsText(file);
}

function importGeoJSON(file) {
    const reader = new FileReader();

    reader.onload = function (e) {
        const data = JSON.parse(e.target.result);

        // remove old AOI
        if (aoiLayer) {
            map.removeLayer(aoiLayer);
        }

        // add layer
        aoiLayer = L.geoJSON(data, {
            style: { color: "#0d6efd", weight: 2, fillOpacity: 0.1 },
        }).addTo(map);

        // zoom
        map.fitBounds(aoiLayer.getBounds());

        // extract geometry properly
        let geometry = null;

        if (data.type === "Feature") {
            geometry = data.geometry;
        } else if (data.type === "FeatureCollection") {
            geometry = data.features[0].geometry;
        } else if (data.type === "Polygon" || data.type === "MultiPolygon") {
            geometry = data;
        }

        if (!geometry) {
            alert("Invalid GeoJSON format");
            return;
        }

        // save states
        originalAOI = {
            type: "Feature",
            geometry: geometry
        };

        finalAOIGeometry = geometry;

        // force NEW project
        CURRENT_PROJECT_ID = null;
        document.getElementById("projectSelect").value = "";

        // create center marker
        const center = aoiLayer.getBounds().getCenter();

        if (marker) {
            map.removeLayer(marker);
        }

        marker = L.marker(center).addTo(map);

        // UI update
        document.getElementById("aoiControlSection").style.display = "grid";
        editBtn.disabled = false;
        resetBtn.disabled = false;

        document.getElementById("status").innerText =
            "AOI imported from GeoJSON ✔";
    };

    reader.readAsText(file);
}

function enableSaveProject() {
    document.getElementById("saveProjectBtn").disabled = false;
}