function samplingIcon(p) {
    let color = "#6c757d";

    if (p.survey_status === "draft") {
        color = "#0d6efd";
    } else if (p.survey_status === "ready") {
        if (p.assigned_count === 0) {
            color = "#8B5A2B";
        } else if (p.assigned_count < p.max_surveyors) {
            color = "#fd7e14";
        } else {
            color = "#6f42c1";
        }
    } else if (p.survey_status === "submitted") {
        color = "#dc3545";
    } else if (p.survey_status === "approved") {
        color = "#198754";
    } else if (p.survey_status === "rejected") {
        color = "#ffc107";
    }

    return L.divIcon({
        className: "sampling-marker",
        html: `<div style="
      background:${color};
      width:14px;
      height:14px;
      border-radius:50%;
      border:2px solid white;"></div>`,
    });
}

// function createSamplingLayer(onEachFeatureCallback) {
//     return L.geoJSON(null, {
//         pointToLayer: (feature, latlng) => {
//             return L.marker(latlng, {
//                 icon: samplingIcon(feature.properties),
//             });
//         },
//         onEachFeature: onEachFeatureCallback,
//     });
// }

function createSamplingLayer(onEachFeatureCallback) {
    return L.geoJSON(null, {
        pointToLayer: (feature, latlng) => {
            return L.marker(latlng, {
                icon: samplingIcon(feature.properties),
            });
        },

        // 🔥 TAMBAHKAN INI
        style: function (feature) {
            return {
                color: "#0d6efd",
                weight: 2,
                fillColor: "#0d6efd",
                fillOpacity: 0.1
            };
        },

        onEachFeature: onEachFeatureCallback,
    });
}