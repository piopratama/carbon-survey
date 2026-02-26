window.SurveyorApp = (function () {
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

    let samplingLayer = createSamplingLayer((feature, layer) => {
        layer.bindPopup(buildPopup(feature.properties, currentUser));
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

    async function selectProject() {
        const mobile = document.getElementById("projectSelect");
        const desktop = document.getElementById("projectSelectDesktop");

        const id = mobile?.value || desktop?.value;
        if (!id) return;

        CURRENT_PROJECT_ID = id;

        await loadSamplingToLayer(id, samplingLayer, map);
    }

    loadProjectsToSelects(["projectSelect", "projectSelectDesktop"]);

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