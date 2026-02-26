function openAssignModal(pointId) {
    document.getElementById("assignPointId").value = pointId;

    loadAvailableSurveyors();
    loadAssignedSurveyors(pointId);

    const modalEl = document.getElementById("assignSurveyModal");

    if (!modalEl) {
        alert("Modal tidak ditemukan di HTML");
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function loadAvailableSurveyors() {
    const res = await fetch(`${API_BASE}/users?role=surveyor`);
    const users = await res.json();

    const select = document.getElementById("availableSurveyors");
    select.innerHTML = "";

    users.forEach((u) => {
        const opt = document.createElement("option");
        opt.value = u.id;
        opt.textContent = u.name;
        select.appendChild(opt);
    });
}

async function loadAssignedSurveyors(pointId) {
    const listEl = document.getElementById("assignedSurveyors");

    if (!listEl) {
        console.error("assignedSurveyors element tidak ditemukan");
        return;
    }

    listEl.innerHTML = "Loading...";

    const res = await fetch(`${API_BASE}/sampling/assigned/${pointId}`);
    const data = await res.json();

    listEl.innerHTML = "";

    if (!data.length) {
        listEl.innerHTML =
            "<small class='text-muted'>Belum ada surveyor</small>";
        return;
    }

    data.forEach((s) => {
        listEl.innerHTML += `
            <div class="d-flex justify-content-between mb-1">
              <span>${s.name}</span>
              <button class="btn btn-sm btn-danger"
                onclick="removeSurveyor(${pointId}, '${s.id}')">
                Hapus
              </button>
            </div>
          `;
    });
}

async function assignSurveyorToPoint() {
    const pointId = document.getElementById("assignPointId").value;
    const surveyorId = document.getElementById("surveyorSelect").value;

    const res = await fetch(`${API_BASE}/sampling/assign/${pointId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ surveyor_id: surveyorId }),
    });

    if (!res.ok) {
        alert("Gagal assign");
        return;
    }

    await loadSamplingPoints(CURRENT_PROJECT_ID);
    loadAssignedSurveyors(pointId);
}

async function assignSurveyor() {
    const pointId = document.getElementById("assignPointId").value;
    const surveyorId = document.getElementById("availableSurveyors").value;

    if (!surveyorId) {
        alert("Pilih surveyor terlebih dahulu");
        return;
    }

    const res = await fetch(`${API_BASE}/sampling/assign/${pointId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ surveyor_id: surveyorId }),
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Gagal assign surveyor");
        return;
    }

    await loadAssignedSurveyors(pointId);
    await loadSamplingPoints(CURRENT_PROJECT_ID);
}

async function assignSurveyorToPoint() {
    const pointId = document.getElementById("assignPointId").value;
    const surveyorId = document.getElementById("surveyorSelect").value;

    const res = await fetch(`${API_BASE}/sampling/assign/${pointId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ surveyor_id: surveyorId }),
    });

    if (!res.ok) {
        alert("Gagal assign");
        return;
    }

    await loadSamplingPoints(CURRENT_PROJECT_ID);
    loadAssignedSurveyors(pointId);
}

async function removeSurveyor(pointId, surveyorId) {
    await fetch(`${API_BASE}/sampling/assign/${pointId}/${surveyorId}`, {
        method: "DELETE",
    });

    await loadSamplingPoints(CURRENT_PROJECT_ID);
    loadAssignedSurveyors(pointId);
}