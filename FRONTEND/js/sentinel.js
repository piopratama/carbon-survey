async function loadSentinelPreview() {
    if (!finalAOIGeometry) return;

    const payload = {
        geometry: finalAOIGeometry,
        year: Number(yearInput.value),
        months: monthsInput.value.split(",").map((m) => Number(m.trim())),
        cloud: Number(cloudInput.value),
    };

    statusEl.textContent = "Memuat Sentinel...";

    const res = await fetch(`${API_BASE}/sentinel/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (sentinelTrueColor) map.removeLayer(sentinelTrueColor);
    if (sentinelNDVI) map.removeLayer(sentinelNDVI);
    if (sentinelControl) map.removeControl(sentinelControl);

    sentinelTrueColor = L.tileLayer(data.true_color_url);
    sentinelNDVI = L.tileLayer(data.ndvi_url, { opacity: 0.8 });

    sentinelTrueColor.addTo(map);

    sentinelControl = L.control
        .layers(null, {
            "Sentinel True Color": sentinelTrueColor,
            NDVI: sentinelNDVI,
        })
        .addTo(map);

    statusEl.textContent = "Sentinel berhasil dimuat.";
}