AdminApp.samplingPopupHTML = function (p) {

    let actions = "";

    const progress = p.survey_status;
    const approval = p.approval_status;

    const assigned = p.assigned_count ?? 0;
    const maxSurveyor = p.max_surveyors ?? 0;

    const start = p.start_date
        ? new Date(p.start_date).toLocaleDateString()
        : "-";

    const end = p.end_date
        ? new Date(p.end_date).toLocaleDateString()
        : "-";

    const surveyDate = p.survey_date
        ? new Date(p.survey_date).toLocaleDateString()
        : "-";

    const totalBiomass = Number(p.total_biomass || 0).toFixed(2);

    // =========================
    // STATUS BADGE
    // =========================

    let approvalBadge = "-";

    if (approval && approval !== "none") {
        let color = "secondary";
        if (approval === "submitted") color = "danger";
        if (approval === "approved") color = "success";
        if (approval === "rejected") color = "warning";

        approvalBadge = `<span class="badge bg-${color}">${approval}</span>`;
    }

    const progressBadge = `
        <span class="badge bg-info">${progress}</span>
    `;

    // =========================
    // LOCK RULE
    // =========================

    const isLocked = approval === "approved" || progress === "expired";

    const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
    const isAdmin = currentUser.role === "admin";

    // =========================
    // ACTION BUTTONS
    // =========================

    if (!isLocked) {

        actions += `
            <button class="btn btn-sm btn-dark w-100 mb-1"
              onclick="AdminApp.openSurveyTreePage(${p.id})">
              View Trees
            </button>
        `;

        // ADMIN REVIEW SECTION
        if (isAdmin && progress === "submitted") {

            actions += `
                <button class="btn btn-sm btn-success w-100 mb-1"
                  onclick="AdminApp.approvePoint(${p.id})">
                  Approve Survey
                </button>

                <button class="btn btn-sm btn-warning w-100 mb-1"
                  onclick="AdminApp.rejectPoint(${p.id})">
                  Reject Survey
                </button>
            `;

        } else if (progress === "draft") {

            actions += `
                <button class="btn btn-sm btn-secondary w-100 mb-1"
                  onclick="openSurveySetup(${p.id})">
                  Setup Survey
                </button>

                <button class="btn btn-sm btn-danger w-100"
                  onclick="AdminApp.deletePoint(${p.id})">
                  Delete Sampling Point
                </button>
            `;
        }

        if (progress !== "draft") {

            actions += `
                <button class="btn btn-sm btn-secondary w-100 mb-1"
                  onclick="openSurveySetup(${p.id}, true)">
                  Edit Survey
                </button>

                <button class="btn btn-sm btn-primary w-100"
                  onclick="openAssignModal(${p.id})">
                  Manage Surveyor
                </button>
            `;
        }

    } else {

        actions = `
            <span class="text-muted small">
              Survey terkunci (final)
            </span>
        `;
    }

    // =========================
    // RETURN HTML
    // =========================

    return `
        <div style="min-width:280px">

            <h6 class="mb-2">Sampling Point #${p.id}</h6>

            <table class="table table-sm table-bordered small mb-2">
                <tbody>
                    <tr>
                        <th width="110">Progress</th>
                        <td>${progressBadge}</td>
                    </tr>
                    <tr>
                        <th>Approval</th>
                        <td>${approvalBadge}</td>
                    </tr>
                    <tr>
                        <th>Latitude</th>
                        <td>${p.latitude?.toFixed(6)}</td>
                    </tr>
                    <tr>
                        <th>Longitude</th>
                        <td>${p.longitude?.toFixed(6)}</td>
                    </tr>
                    <tr>
                        <th>Surveyor</th>
                        <td>${assigned} / ${maxSurveyor}</td>
                    </tr>
                    <tr>
                        <th>Period</th>
                        <td>${start} - ${end}</td>
                    </tr>
                    <tr>
                        <th>Survey Date</th>
                        <td>${surveyDate}</td>
                    </tr>
                    <tr>
                        <th>Total Biomass</th>
                        <td><strong>${totalBiomass} kg</strong></td>
                    </tr>
                </tbody>
            </table>

            <div class="d-grid gap-1">
                ${actions}
            </div>

        </div>
    `;
};