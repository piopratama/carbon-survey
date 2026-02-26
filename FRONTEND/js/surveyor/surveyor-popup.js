function buildPopup(p, currentUser) {
    const joined = p.assigned_ids?.includes(currentUser?.id);
    const full = p.assigned_count >= p.max_surveyors;

    let buttons = "";

    if (!joined && !full) {
        buttons += `
      <button class="btn btn-sm btn-primary w-100 mt-2"
        onclick="joinSurvey(${p.id})">
        Join
      </button>`;
    }

    if (joined) {
        buttons += `
      <button class="btn btn-sm btn-danger w-100 mt-2"
        onclick="leaveSurvey(${p.id})">
        Leave
      </button>

      <button class="btn btn-sm btn-success w-100 mt-2"
        onclick="SurveyorApp.openSurveyTreePage(${p.id})">
        Input Measurement
      </button>`;
    }

    let assignedList = "<span class='text-muted'>Belum ada</span>";

    if (p.assigned_names && p.assigned_names.length > 0) {
        assignedList = `
      <ol class="mb-1 ps-3">
        ${p.assigned_names.map((name) => `<li>${name}</li>`).join("")}
      </ol>
    `;
    }

    return `
  <div style="min-width:260px">
    <table class="table table-sm table-borderless mb-1">
      <tr><td><strong>ID</strong></td><td>${p.id}</td></tr>
      <tr><td><strong>Status</strong></td><td>${p.survey_status}</td></tr>
      <tr><td><strong>Latitude</strong></td>
        <td>${p.latitude?.toFixed(6)}</td></tr>
      <tr><td><strong>Longitude</strong></td>
        <td>${p.longitude?.toFixed(6)}</td></tr>
      <tr><td><strong>Capacity</strong></td>
        <td>${p.assigned_count}/${p.max_surveyors}</td></tr>
      <tr>
        <td><strong>Total Biomass</strong></td>
        <td>${(p.total_biomass || 0).toFixed(2)} kg</td>
      </tr>
      <tr>
        <td class="align-top"><strong>Surveyors</strong></td>
        <td>${assignedList}</td>
      </tr>
    </table>
    ${buttons}
  </div>`;
}