window.SurveyorApp = (function () {
    let projectAOILayer = null; // taruh di atas (global)
    const currentUser = JSON.parse(localStorage.getItem("user"));

    let CURRENT_PROJECT_ID = null;
    let CURRENT_SURVEY_LAT = null;
    let CURRENT_SURVEY_LNG = null;
    let CURRENT_POINT_DATA = null;
    let SPECIES_DATA = [];

    /* ============================= */
    /* MAP */
    /* ============================= */

    const map = L.map("map").setView([-2, 118], 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(
        map,
    );

    // let samplingLayer = createSamplingLayer((feature, layer) => {
    //     layer.bindPopup(buildPopup(feature.properties, currentUser));
    // }).addTo(map);
    let samplingLayer = createSamplingLayer((feature, layer) => {
        const p = feature.properties;

        layer.bindPopup(buildPopup(p, currentUser));

        // ADD THESE 4 LINES ONLY
        layer.unbindTooltip();

        if (window.SurveyorApp?.showPointId !== false) {
            layer.bindTooltip(`${p.id}`, {
                permanent: true,
                direction: "top"
            });
        }

    }).addTo(map);

    /* ============================= */
    /* POPUP */
    /* ============================= */

    function openSurveyTreePage(pointId) {
        window.location.href = `survey_tree.html?point_id=${pointId}`;
    }

    /* ============================= */
    /* MODAL */
    /* ============================= */

    function openSurveyModal(id, lat, lng, data) {
        CURRENT_SURVEY_LAT = lat;
        CURRENT_SURVEY_LNG = lng;
        CURRENT_POINT_DATA = data;

        document.getElementById("measurementPointId").value = id;
        document.getElementById("surveyDescription").innerText =
            data.description || "No description";

        loadSpecies();

        new bootstrap.Modal(document.getElementById("measurementModal")).show();
    }

    async function loadSpecies() {
        const res = await fetch(`${API_BASE}/tree-species`);
        const data = await res.json();

        SPECIES_DATA = data;

        const select = document.getElementById("speciesSelect");
        select.innerHTML = `<option value="">-- Select Species --</option>`;

        data.forEach((s) => {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = s.name;
            select.appendChild(opt);
        });

        select.onchange = showSpeciesDetail;
    }

    function showSpeciesDetail() {
        const id = document.getElementById("speciesSelect").value;
        const species = SPECIES_DATA.find((s) => s.id == id);
        const box = document.getElementById("speciesDetailBox");

        if (!species) {
            box.style.display = "none";
            return;
        }

        document.getElementById("speciesName").innerText = species.name;
        document.getElementById("speciesLatin").innerText =
            species.latin_name || "";
        document.getElementById("speciesDescription").innerText =
            species.description || "No description";
        document.getElementById("speciesExtra").innerText = species.family
            ? `Family: ${species.family}`
            : "";

        box.style.display = "block";
    }

    /* ============================= */
    /* SUBMIT */
    /* ============================= */

    async function submitMeasurement() {
        const pointId = document.getElementById("measurementPointId").value;

        const payload = {
            surveyor_id: currentUser.id,
            latitude: CURRENT_SURVEY_LAT,
            longitude: CURRENT_SURVEY_LNG,
            species_id: document.getElementById("speciesSelect").value,
            dbh: document.getElementById("dbhInput").value,
            height: document.getElementById("heightInput").value,
            notes: document.getElementById("notesInput").value,
        };

        const res = await fetch(`${API_BASE}/survey/submit-tree/${pointId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            alert("Failed");
            return;
        }

        alert("Saved");
        bootstrap.Modal.getInstance(
            document.getElementById("measurementModal"),
        ).hide();
    }

    /* ============================= */
    /* PROJECT */
    /* ============================= */

    // async function selectProject(selectedId) {
    //     console.log(" selectProject TRIGGERED", selectedId);
    //     const mobile = document.getElementById("projectSelectMobile");
    //     const desktop = document.getElementById("projectSelectDesktop");

    //     console.log("Selected project:", mobile?.value, desktop?.value);

    //     const id = mobile?.value || desktop?.value;
    //     if (!id) return;

    //     CURRENT_PROJECT_ID = id;

    //     await loadSamplingToLayer(id, samplingLayer, map);
    // }

    // async function selectProject(selectedId) {
    //     if (!selectedId) return;

    //     CURRENT_PROJECT_ID = selectedId;

    //     await loadSamplingToLayer(selectedId, samplingLayer, map);
    // }

    // async function selectProject(selectedId) {
    //     if (!selectedId) return;

    //     CURRENT_PROJECT_ID = selectedId;

    //     // HAPUS AOI lama
    //     if (projectAOILayer) {
    //         map.removeLayer(projectAOILayer);
    //         projectAOILayer = null;
    //     }

    //     // AMBIL PROJECT (yang ada AOI)
    //     const res = await fetch(`${API_BASE}/projects`);
    //     const projects = await res.json();

    //     const project = projects.find(p => p.id === selectedId);

    //     // TAMBAHKAN POLYGON
    //     if (project?.aoi) {
    //         projectAOILayer = L.geoJSON({
    //             type: "Feature",
    //             geometry: project.aoi
    //         }, {
    //             style: {
    //                 color: "#dc3545",
    //                 weight: 2,
    //                 fillOpacity: 0.05
    //             }
    //         }).addTo(map);
    //     }

    //     // LOAD SAMPLING POINT (yang sudah ada)
    //     await loadSamplingToLayer(selectedId, samplingLayer, map);
    // }

    async function selectProject(selectedId) {
        if (!selectedId) return;

        CURRENT_PROJECT_ID = selectedId;

        // HAPUS AOI lama
        if (projectAOILayer) {
            map.removeLayer(projectAOILayer);
            projectAOILayer = null;
        }

        // AMBIL PROJECT
        const res = await fetch(`${API_BASE}/projects`);
        const projects = await res.json();
        const project = projects.find(p => p.id === selectedId);

        // TAMBAHKAN POLYGON
        if (project?.aoi) {
            projectAOILayer = L.geoJSON({
                type: "Feature",
                geometry: project.aoi
            }, {
                style: {
                    color: "#dc3545",
                    weight: 2,
                    fillOpacity: 0.05
                }
            }).addTo(map);
        }

        // LOAD SAMPLING
        await loadSamplingToLayer(selectedId, samplingLayer, map);

        // FIX: kalau tidak ada sampling, zoom ke polygon
        if (samplingLayer.getLayers().length === 0 && projectAOILayer) {
            map.fitBounds(projectAOILayer.getBounds(), {
                padding: [40, 40],
                maxZoom: 18
            });
        }
    }

    //loadProjectsToSelects(["projectSelect", "projectSelectDesktop"]);
    // loadProjectsToSelects(["projectSelectMobile", "projectSelectDesktop"]).then(() => {

    //     const projectId = localStorage.getItem("current_project_id");

    //     if (!projectId) return;

    //     const mobile = document.getElementById("projectSelectMobile");
    //     const desktop = document.getElementById("projectSelectDesktop");

    //     if (mobile) mobile.value = projectId;
    //     if (desktop) desktop.value = projectId;

    //     selectProject();

    // });

    loadProjectsToSelects(["projectSelectMobile", "projectSelectDesktop"]).then(() => {
        const projectId = localStorage.getItem("current_project_id");
        if (!projectId) return;

        const mobile = document.getElementById("projectSelectMobile");
        const desktop = document.getElementById("projectSelectDesktop");

        if (mobile) mobile.value = projectId;
        if (desktop) desktop.value = projectId;

        selectProject(projectId);
    });

    /* ============================= */
    /* JOIN / LEAVE */
    /* ============================= */

    window.joinSurvey = async function (pointId) {
        const res = await fetch(`${API_BASE}/sampling/assign/${pointId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                surveyor_id: currentUser.id,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.detail || "Failed to join");
            return;
        }

        alert("Joined successfully");

        // reload current project layer
        if (CURRENT_PROJECT_ID) {
            selectProject();
        }
    };

    window.leaveSurvey = async function (pointId) {
        const res = await fetch(
            `${API_BASE}/sampling/assign/${pointId}/${currentUser.id}`,
            {
                method: "DELETE",
            },
        );

        const data = await res.json();

        if (!res.ok) {
            alert(data.detail || "Failed to leave");
            return;
        }

        alert("Left successfully");

        if (CURRENT_PROJECT_ID) {
            selectProject();
        }
    };

    return {
        selectProject,
        submitMeasurement,
        openSurveyTreePage,
    };

})();


window.SurveyorApp = window.SurveyorApp || {};
window.SurveyorApp.showPointId =
    localStorage.getItem("showPointId") !== "false";

window.SurveyorApp.togglePointIdVisibility = function (isVisible) {
    localStorage.setItem("showPointId", isVisible); // save state
    location.reload();
};