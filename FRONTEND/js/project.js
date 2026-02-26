function initPage() {
    // reset variabel global
    marker = null;
    aoiLayer = null;
    originalAOI = null;
    editHandler = null;
    projectAOILayer = null;
    finalAOIGeometry = null;

    sentinelTrueColor = null;
    sentinelNDVI = null;
    sentinelControl = null;

    CURRENT_PROJECT_ID = null;
    projectMap = {};
    MANUAL_MODE_ACTIVE = false;

    // reset UI
    document.getElementById("searchInput").value = "";
    document.getElementById("projectNameInput").value = "";
    document.getElementById("projectSelect").value = "";

    document.getElementById("samplingSection").style.display = "none";
    document.getElementById("sentinelSection").style.display = "none";
    document.getElementById("aoiControlSection").style.display = "none";

    document.getElementById("samplingPreview").innerText = "Belum dihitung";

    editBtn.disabled = true;
    resetBtn.disabled = true;
    saveBtn.disabled = true;

    statusEl.textContent = "Silakan cari lokasi.";

    // reset map view
    map.setView([-2, 118], 5);
}

function startNewProject() {
    // reset project selection
    document.getElementById("projectSelect").value = "";
    CURRENT_PROJECT_ID = null;

    // hapus AOI project lama
    if (projectAOILayer) {
        map.removeLayer(projectAOILayer);
        projectAOILayer = null;
    }

    if (aoiLayer) {
        map.removeLayer(aoiLayer);
        aoiLayer = null;
    }

    if (!marker) {
        alert("Cari lokasi terlebih dahulu");
        return;
    }

    // buat AOI default di sekitar marker
    const { lat, lng } = marker.getLatLng();
    const size = 0.01;

    originalAOI = {
        type: "Feature",
        geometry: {
            type: "Polygon",
            coordinates: [
                [
                    [lng - size, lat - size],
                    [lng + size, lat - size],
                    [lng + size, lat + size],
                    [lng - size, lat + size],
                    [lng - size, lat - size],
                ],
            ],
        },
    };

    aoiLayer = L.geoJSON(originalAOI, {
        style: { color: "#0d6efd", weight: 2, fillOpacity: 0.1 },
    }).addTo(map);

    map.fitBounds(aoiLayer.getBounds());

    // tampilkan kontrol AOI
    document.getElementById("aoiControlSection").style.display = "grid";

    // aktifkan edit mode langsung
    editBtn.disabled = false;
    resetBtn.disabled = false;
    enableEditAOI();

    // reset state
    finalAOIGeometry = null;
    document.getElementById("projectNameInput").value = "";
    document.getElementById("saveProjectBtn").disabled = false;

    // sembunyikan downstream
    document.getElementById("samplingSection").style.display = "none";
    document.getElementById("sentinelSection").style.display = "none";

    statusEl.textContent =
        "Mode project baru: edit area fokus lalu simpan project.";
}

async function loadProjects() {
    const res = await fetch(`${API_BASE}/projects`);
    const projects = await res.json(); // <-- projects DIDEFINISIKAN DI SINI

    const select = document.getElementById("projectSelect");
    select.innerHTML = `<option value="">-- Select Project --</option>`;

    projectMap = {}; // reset

    projects.forEach((p) => {
        projectMap[p.id] = p;

        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.year})`;
        select.appendChild(opt);
    });

    const savedProject = getCurrentProject();

    if (savedProject && projectMap[savedProject]) {
        select.value = savedProject;
        selectProject();
    }
}

function selectProject() {
    const select = document.getElementById("projectSelect");
    const projectId = select.value;
    if (!projectId) return;

    const project = projectMap[projectId];
    if (!project || !project.center || !project.aoi) {
        alert("Data area project tidak tersedia");
        return;
    }

    CURRENT_PROJECT_ID = projectId;
    setCurrentProject(projectId);

    // Hapus AOI lama
    if (projectAOILayer) {
        map.removeLayer(projectAOILayer);
        projectAOILayer = null;
    }

    document.getElementById("aoiControlSection").style.display = "grid";
    editBtn.disabled = false;
    resetBtn.disabled = false;
    //enableEditAOI();
    document.getElementById("aoiControlSection").style.display = "grid";
    editBtn.disabled = false;
    resetBtn.disabled = false;

    // Tambahkan AOI baru
    projectAOILayer = L.geoJSON(
        {
            type: "Feature",
            geometry: project.aoi,
        },
        {
            style: {
                color: "#dc3545", // merah (area fokus)
                weight: 2,
                fillOpacity: 0.05,
                dashArray: "4,4",
            },
        },
    ).addTo(map);

    finalAOIGeometry = project.aoi;

    map.fitBounds(projectAOILayer.getBounds());

    AdminApp.loadSamplingPoints(projectId);

    statusEl.textContent = `Project aktif: ${project.name}`;
    document.getElementById("samplingSection").style.display = "block";
    document.getElementById("sentinelSection").style.display = "block";

    document.querySelector(
        'input[name="samplingMode"][value="grid"]',
    ).checked = true;

    if (window.AdminApp && AdminApp.onSamplingModeChange) {
        AdminApp.onSamplingModeChange();
    }
}

async function saveProject() {
    if (!aoiLayer) {
        alert("Area fokus belum ada");
        return;
    }

    if (isEditModeActive()) {
        alert("Selesaikan edit area terlebih dahulu");
        return;
    }

    const name = document.getElementById("projectNameInput").value.trim();
    if (!name) {
        alert("Nama project wajib diisi");
        return;
    }

    const geo = aoiLayer.toGeoJSON();
    const feature = geo.features ? geo.features[0] : geo;

    const payload = {
        name,
        geometry: feature.geometry,
        year: Number(document.getElementById("yearInput").value),
        months: document
            .getElementById("monthsInput")
            .value.split(",")
            .map((m) => Number(m.trim()))
            .filter((x) => !Number.isNaN(x)),
        cloud: Number(document.getElementById("cloudInput").value),
    };

    const isUpdate = !!CURRENT_PROJECT_ID;
    const url = isUpdate
        ? `${API_BASE}/projects/${CURRENT_PROJECT_ID}`
        : `${API_BASE}/projects`;

    const method = isUpdate ? "PUT" : "POST";

    statusEl.textContent = isUpdate
        ? "Memperbarui project..."
        : "Menyimpan project...";

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Gagal menyimpan project");
        statusEl.textContent = "Gagal menyimpan project.";
        return;
    }

    // reload list
    await loadProjects();

    // set & select project
    CURRENT_PROJECT_ID = data.id;
    const select = document.getElementById("projectSelect");
    select.value = data.id;

    selectProject();

    statusEl.textContent = isUpdate
        ? "Project berhasil diperbarui"
        : "Project berhasil disimpan";
}

async function deleteProject() {
    if (!CURRENT_PROJECT_ID) return;

    if (!confirm("Hapus project DAN semua sampling point?")) return;

    // delete backend
    await fetch(`${API_BASE}/projects/${CURRENT_PROJECT_ID}`, {
        method: "DELETE",
    });

    // bersihkan AOI project di map (PENTING)
    if (projectAOILayer) {
        map.removeLayer(projectAOILayer);
        projectAOILayer = null;
    }

    // reset semua state frontend
    CURRENT_PROJECT_ID = null;
    projectMap = {};

    resetAll();

    // reload project list (tunggu sampai selesai)
    await loadProjects();

    statusEl.textContent = "Project dihapus.";
}

function resetAll() {
    // Disable edit mode
    if (editHandler) {
        editHandler.disable();
        editHandler = null;
        editBtn.textContent = "Edit Area";
    }

    // Reset project state
    CURRENT_PROJECT_ID = null;

    // Remove marker
    if (marker) {
        map.removeLayer(marker);
        marker = null;
    }

    // Remove AOI
    if (aoiLayer) {
        map.removeLayer(aoiLayer);
        aoiLayer = null;
    }

    originalAOI = null;
    finalAOIGeometry = null;

    // Remove Sentinel layers
    if (sentinelTrueColor) {
        map.removeLayer(sentinelTrueColor);
        sentinelTrueColor = null;
    }

    if (sentinelNDVI) {
        map.removeLayer(sentinelNDVI);
        sentinelNDVI = null;
    }

    if (sentinelControl) {
        map.removeControl(sentinelControl);
        sentinelControl = null;
    }

    // Clear sampling points
    samplingLayer.clearLayers();

    // Hide Sentinel section
    document.getElementById("sentinelSection").style.display = "none";

    // Reset inputs
    document.getElementById("searchInput").value = "";
    document.getElementById("yearInput").value = 2024;
    document.getElementById("monthsInput").value = "6,7,8";
    document.getElementById("cloudInput").value = 20;
    document.getElementById("projectNameInput").value = "";

    // Reset project select
    document.getElementById("projectSelect").value = "";

    // Disable buttons
    editBtn.disabled = true;
    resetBtn.disabled = true;
    document.getElementById("saveProjectBtn").disabled = true;

    // Reset status
    statusEl.textContent = "Silakan cari lokasi.";

    document.getElementById("samplingSection").style.display = "none";
    document.getElementById("samplingPreview").innerText = "Belum dihitung";
    document.getElementById("sentinelSection").style.display = "none";
    document.getElementById("aoiControlSection").style.display = "none";

    // hapus AOI project jika masih ada
    if (projectAOILayer) {
        map.removeLayer(projectAOILayer);
        projectAOILayer = null;
    }

    // Reset map view
    map.setView([-2, 118], 5);
}

projectNameInput.addEventListener("input", () => {
    if (!aoiLayer) {
        saveBtn.disabled = true;
        return;
    }

    if (isEditModeActive()) {
        saveBtn.disabled = true;
        return;
    }

    saveBtn.disabled = projectNameInput.value.trim() === "";
});