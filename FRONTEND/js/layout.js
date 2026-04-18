// ===== LOAD PARTIAL =====
async function loadPartial(id, file) {
    const el = document.getElementById(id);
    if (!el) return;

    try {
        const res = await fetch(file);
        const html = await res.text();
        el.innerHTML = html;

        if (id === "header") {
            initHeaderLogic();
        }
    } catch (err) {
        console.error("Failed to load partial:", file, err);
    }
}

// ===== HEADER LOGIC =====
function initHeaderLogic() {
    const user = window.currentUser;
    if (!user) return;

    // user info
    const userInfo = document.getElementById("userInfo");
    if (userInfo) {
        userInfo.innerText = `${user.name} (${user.role})`;
    }

    // hide admin-only
    if (user.role !== "admin") {
        document.querySelectorAll(".admin-only").forEach((el) => el.remove());
    }

    // hide surveyor-only
    if (user.role !== "surveyor") {
        document.querySelectorAll(".surveyor-only").forEach((el) => el.remove());
    }

    // active link highlight
    const current = window.location.pathname.split("/").pop();
    document.querySelectorAll(".nav-link").forEach((link) => {
        if (link.getAttribute("href") === current) {
            link.classList.add("active");
        }
    });
}

// ===== GLOBAL ACTIONS =====
window.logout = function () {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
};

window.goHome = function (e) {
    if (e) e.preventDefault();

    const user = window.currentUser;

    if (!user) {
        window.location.href = "index.html";
        return;
    }

    if (user.role === "admin") {
        window.location.href = "main.html";
    } else if (user.role === "surveyor") {
        window.location.href = "surveyor_main.html";
    } else {
        window.location.href = "index.html";
    }
};

// ===== INIT (SAFE: SCRIPT AT BOTTOM) =====
loadPartial("header", "partials/header.html");
loadPartial("footer", "partials/footer.html");