async function loadPartial(id, file) {
    const res = await fetch(file);
    const html = await res.text();
    document.getElementById(id).innerHTML = html;

    if (id === "header") {
        initHeaderLogic();
    }
}

function initHeaderLogic() {
    const userData = localStorage.getItem("user");
    if (!userData) return;

    const currentUser = JSON.parse(userData);

    // tampilkan user info
    const userInfo = document.getElementById("userInfo");
    if (userInfo) {
        userInfo.innerText = currentUser.name + " (" + currentUser.role + ")";
    }

    // hide admin menu
    if (currentUser.role !== "admin") {
        document.querySelectorAll(".admin-only").forEach((el) => el.remove());
    }

    // hide surveyor menu
    if (currentUser.role !== "surveyor") {
        document
            .querySelectorAll(".surveyor-only")
            .forEach((el) => el.remove());
    }

    // highlight active link
    const current = window.location.pathname.split("/").pop();
    document.querySelectorAll(".nav-link").forEach((link) => {
        if (link.getAttribute("href") === current) {
            link.classList.add("active");
        }
    });
}

window.logout = function () {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
};

loadPartial("header", "partials/header.html");
loadPartial("footer", "partials/footer.html");