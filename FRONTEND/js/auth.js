// ===== AUTH CHECK (NO DOM USAGE) =====

(function () {
    const token = localStorage.getItem("token");
    const userData = localStorage.getItem("user");

    let currentUser = null;

    try {
        currentUser = userData ? JSON.parse(userData) : null;
    } catch (e) {
        currentUser = null;
    }

    // ===== REQUIRE LOGIN =====
    if (!token || !currentUser) {
        window.location.href = "index.html";
        return;
    }

    // ===== REQUIRE ROLE =====
    if (window.REQUIRED_ROLE) {
        const allowed = Array.isArray(window.REQUIRED_ROLE)
            ? window.REQUIRED_ROLE
            : [window.REQUIRED_ROLE];

        if (!allowed.includes(currentUser.role)) {
            window.location.href = "index.html";
            return;
        }
    }

    // expose globally
    window.currentUser = currentUser;
})();