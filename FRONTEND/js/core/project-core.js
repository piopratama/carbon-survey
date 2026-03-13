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

    //loadSamplingToLayer(selectIds, samplingLayer, map);
}

// async function loadSamplingToLayer(projectId, layer, mapInstance) {
//     if (!projectId) return;

//     const res = await fetch(`${API_BASE}/sampling/points/${projectId}`);
//     const geojson = await res.json();

//     layer.clearLayers();
//     layer.addData(geojson);

//     if (layer.getLayers().length > 0) {
//         mapInstance.fitBounds(layer.getBounds());
//     }
// }

async function loadSamplingToLayer(projectId, layer, mapInstance) {

    if (!projectId) return;

    const res = await fetch(`${API_BASE}/sampling/points/${projectId}`);
    const geojson = await res.json();

    layer.clearLayers();
    layer.addData(geojson);

    const layers = layer.getLayers();

    if (layers.length === 0) return;

    // ensure map size correct
    mapInstance.invalidateSize();

    if (layers.length === 1) {

        const latlng = layers[0].getLatLng();

        mapInstance.setView(latlng, 18);

    } else {

        mapInstance.fitBounds(layer.getBounds(), {
            padding: [40, 40],
            maxZoom: 18
        });

    }

}