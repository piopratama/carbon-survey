function openSurveySetup(pointId, isEdit = false) {
    document.getElementById("setupPointId").value = pointId;

    // cari feature dari samplingLayer
    const geo = AdminApp.samplingLayer.toGeoJSON();
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