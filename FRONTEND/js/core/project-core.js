async function loadProjectsToSelects(selectIds) {
    const res = await fetch(`${API_BASE}/projects/`);
    const projects = await res.json();

    selectIds.forEach((id) => {
        const select = document.getElementById(id);
        if (!select) return;

        select.innerHTML = `<option value="">-- Select Project --</option>`;

        projects.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = `${p.name} (${p.year})`;
            select.appendChild(opt);
        });
    });
}

async function loadSamplingToLayer(projectId, layer, mapInstance) {
    if (!projectId) return;

    const res = await fetch(`${API_BASE}/sampling/points/${projectId}`);
    const geojson = await res.json();

    layer.clearLayers();
    layer.addData(geojson);

    if (layer.getLayers().length > 0) {
        mapInstance.fitBounds(layer.getBounds());
    }
}