const statusEl = document.getElementById("status");
const saveBtn = document.getElementById("saveProjectBtn");

function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
}