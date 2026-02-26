function openSurveySetup(pointId, isEdit = false) {
    document.getElementById("setupPointId").value = pointId;

    // cari feature dari samplingLayer
    const geo = samplingLayer.toGeoJSON();
    const feature = geo.features.find((f) => f.properties.id == pointId);

    if (!feature) return;

    const p = feature.properties;

    if (isEdit) {
        // isi dengan data lama
        document.getElementById("setupStartDate").value = p.start_date || "";
        document.getElementById("setupEndDate").value = p.end_date || "";
        document.getElementById("setupDescription").value =
            p.description || "";
        document.getElementById("setupMaxSurveyor").value =
            p.max_surveyors || 5;
    } else {
        // kosongkan kalau setup baru
        document.getElementById("setupStartDate").value = "";
        document.getElementById("setupEndDate").value = "";
        document.getElementById("setupDescription").value = "";
        document.getElementById("setupMaxSurveyor").value = 5;
    }

    const modal = new bootstrap.Modal(
        document.getElementById("surveySetupModal"),
    );

    modal.show();
}

async function saveSurveySetup() {
    const pointId = document.getElementById("setupPointId").value;

    const payload = {
        start_date: document.getElementById("setupStartDate").value,
        end_date: document.getElementById("setupEndDate").value,
        description: document.getElementById("setupDescription").value,
        max_surveyors: Number(
            document.getElementById("setupMaxSurveyor").value,
        ),
        plot_radius_m: Number(
            document.getElementById("setupPlotRadius").value,
        ),
    };

    const res = await fetch(`${API_BASE}/sampling/setup/${pointId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        alert("Gagal menyimpan setup");
        return;
    }

    alert("Survey setup berhasil");

    bootstrap.Modal.getInstance(
        document.getElementById("surveySetupModal"),
    ).hide();

    await loadSamplingPoints(CURRENT_PROJECT_ID);
}