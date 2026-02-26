window.AdminApp = (function () {

    let samplingLayer = L.geoJSON(null, {
        pointToLayer: (feature, latlng) => {
            const surveyStatus = feature.properties.survey_status;

            return L.marker(latlng, {
                draggable: surveyStatus === "draft",
                icon: samplingIcon(feature.properties),
            });
        },

        onEachFeature: (feature, layer) => {

            // 🔥 PENTING: pakai AdminApp namespace
            layer.bindPopup(
                AdminApp.samplingPopupHTML(feature.properties)
            );

            if (feature.properties.survey_status === "draft") {
                layer.on("dragend", (e) => {
                    const { lat, lng } = e.target.getLatLng();
                    movePoint(feature.properties.id, lat, lng);
                });
            }
        },
    }).addTo(map);

    L.control
        .layers(null, {
            "Sampling Points": samplingLayer,
        })
        .addTo(map);

    let manualTempLayer = L.geoJSON(null, {
        pointToLayer: (f, latlng) =>
            L.marker(latlng, {
                icon: samplingIcon({
                    survey_status: "draft",
                    assigned_count: 0,
                    max_surveyors: 0,
                    approval_status: null,
                }),
            }),
    }).addTo(map);


    function openSurveyTreePage(pointId) {
        window.location.href = `survey_tree.html?point_id=${pointId}`;
    }


    async function loadSamplingPoints(projectId) {
        await loadSamplingToLayer(projectId, samplingLayer, map);
    }


    async function generateSampling() {
        if (!CURRENT_PROJECT_ID) {
            alert("Pilih project terlebih dahulu");
            return;
        }

        const mode = document.querySelector(
            'input[name="samplingMode"]:checked'
        ).value;

        if (mode !== "grid") {
            alert("Mode ini belum tersedia");
            return;
        }

        const spacing = Number(
            document.getElementById("spacingInput").value
        );

        if (spacing < 10) {
            alert("Jarak terlalu kecil");
            return;
        }

        if (!confirm(
            "Generate sampling grid?\n" +
            "Titik open akan diganti, titik locked tetap."
        )) return;

        statusEl.textContent = "Menghasilkan sampling...";

        await fetch(
            `${API_BASE}/sampling/generate/${CURRENT_PROJECT_ID}?spacing_m=${spacing}`,
            { method: "POST" }
        );

        await loadSamplingPoints(CURRENT_PROJECT_ID);

        statusEl.textContent = "Sampling berhasil dibuat";
    }


    async function previewSampling() {
        if (!CURRENT_PROJECT_ID) {
            alert("Pilih project dulu");
            return;
        }

        const spacing = Number(
            document.getElementById("spacingInput").value
        );

        if (spacing < 10) {
            alert("Spacing terlalu kecil");
            return;
        }

        const el = document.getElementById("samplingPreview");
        el.innerText = "Menghitung...";

        const res = await fetch(
            `${API_BASE}/sampling/preview/${CURRENT_PROJECT_ID}?spacing=${spacing}`
        );

        if (!res.ok) {
            el.innerText = "Gagal menghitung";
            return;
        }

        const data = await res.json();
        el.innerText = `Perkiraan titik: ${data.count} titik`;
    }


    async function deletePoint(pointId) {
        if (!confirm("Hapus titik ini?")) return;

        const res = await fetch(`${API_BASE}/sampling/${pointId}`, {
            method: "DELETE",
        });

        if (!res.ok) {
            alert("Tidak bisa menghapus titik (mungkin terkunci)");
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
    }


    async function movePoint(pointId, lat, lng) {
        const res = await fetch(`${API_BASE}/sampling/${pointId}/move`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat, lng }),
        });

        if (!res.ok) {
            alert("Gagal memindahkan titik");
            await loadSamplingPoints(CURRENT_PROJECT_ID);
            return;
        }

        statusEl.textContent = "Titik dipindahkan";
    }


    async function approvePoint(pointId) {
        if (!confirm("Approve this survey?")) return;

        const res = await fetch(`${API_BASE}/sampling/review/${pointId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "approved" }),
        });

        if (!res.ok) {
            alert("Failed to approve");
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
    }


    async function rejectPoint(pointId) {
        if (!confirm("Reject this survey?")) return;

        const res = await fetch(`${API_BASE}/sampling/review/${pointId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "rejected" }),
        });

        if (!res.ok) {
            alert("Failed to reject");
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
    }


    async function removeAllSampling() {
        if (!CURRENT_PROJECT_ID) {
            alert("Pilih project terlebih dahulu");
            return;
        }

        if (!confirm(
            "Hapus SEMUA sampling point dalam project ini?\n\n" +
            "Titik yang sudah locked / approved mungkin tidak akan terhapus."
        )) return;

        statusEl.textContent = "Menghapus semua sampling point...";

        const res = await fetch(
            `${API_BASE}/sampling/project/${CURRENT_PROJECT_ID}`,
            { method: "DELETE" }
        );

        const data = await res.json();

        if (!res.ok) {
            alert(data.detail || "Gagal menghapus sampling");
            statusEl.textContent = "Gagal menghapus sampling.";
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
        statusEl.textContent = "Semua sampling berhasil dihapus.";
    }


    async function lockPoint(pointId) {
        if (!CURRENT_PROJECT_ID) {
            alert("Project belum aktif");
            return;
        }

        if (!confirm("Kunci titik ini?")) return;

        const res = await fetch(`${API_BASE}/sampling/lock/${pointId}`, {
            method: "POST",
        });

        if (!res.ok) {
            alert("Gagal mengunci titik");
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
    }


    async function unlockPoint(pointId) {
        if (!confirm("Unlock titik ini?")) return;

        const res = await fetch(`${API_BASE}/sampling/unlock/${pointId}`, {
            method: "POST",
        });

        if (!res.ok) {
            alert("Gagal unlock titik");
            return;
        }

        await loadSamplingPoints(CURRENT_PROJECT_ID);
    }


    function onSamplingModeChange() {
        const mode = document.querySelector(
            'input[name="samplingMode"]:checked'
        )?.value;

        const spacingInput = document.getElementById("spacingInput");
        const previewText = document.getElementById("samplingPreview");

        MANUAL_MODE_ACTIVE = false;
        map.off("click", onManualMapClick);
        manualTempLayer.clearLayers();

        if (mode === "grid") {
            spacingInput.disabled = false;
            previewText.innerText = "Belum dihitung";
        }

        if (mode === "manual") {
            if (!CURRENT_PROJECT_ID) {
                alert("Pilih project terlebih dahulu");
                document.querySelector(
                    'input[name="samplingMode"][value="grid"]'
                ).checked = true;
                return;
            }

            spacingInput.disabled = true;
            previewText.innerText = "Klik peta untuk menambah titik";

            MANUAL_MODE_ACTIVE = true;
            map.on("click", onManualMapClick);
        }

        if (mode === "count") {
            spacingInput.disabled = true;
            previewText.innerText = "Mode ini belum tersedia";
        }
    }


    async function onManualMapClick(e) {
        if (!MANUAL_MODE_ACTIVE || !CURRENT_PROJECT_ID) return;

        const { lat, lng } = e.latlng;

        manualTempLayer.addData({
            type: "Feature",
            geometry: {
                type: "Point",
                coordinates: [lng, lat],
            },
        });

        if (!confirm("Tambahkan titik sampling di lokasi ini?")) {
            manualTempLayer.clearLayers();
            return;
        }

        statusEl.textContent = "Menyimpan titik manual...";

        const res = await fetch(
            `${API_BASE}/sampling/manual/${CURRENT_PROJECT_ID}`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ lat, lng }),
            }
        );

        if (!res.ok) {
            alert("Gagal menyimpan titik");
            manualTempLayer.clearLayers();
            return;
        }

        manualTempLayer.clearLayers();
        await loadSamplingPoints(CURRENT_PROJECT_ID);

        statusEl.textContent = "Titik manual ditambahkan";
    }


    return {
        loadSamplingPoints,
        generateSampling,
        previewSampling,
        deletePoint,
        approvePoint,
        rejectPoint,
        movePoint,
        removeAllSampling,
        lockPoint,
        unlockPoint,
        onSamplingModeChange,
        openSurveyTreePage
    };

})();