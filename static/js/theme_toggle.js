document.addEventListener("DOMContentLoaded", () => {

    const root = document.documentElement;

    const toggleBtn = document.getElementById("themeToggle");
    const icon = document.getElementById("themeIcon");

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const getMode = () => localStorage.getItem("themeMode") || "light";

    const applyTheme = (mode) => {
        let theme;

        if (mode === "system") {
            theme = mediaQuery.matches ? "dark" : "light";
        } else {
            theme = mode;
        }

        root.setAttribute("data-bs-theme", theme);
        localStorage.setItem("themeMode", mode);

        if (theme === "dark") {
            icon.classList.remove("fa-sun");
            icon.classList.add("fa-moon");
        } else {
            icon.classList.remove("fa-moon");
            icon.classList.add("fa-sun");
        }
    };

    toggleBtn.addEventListener("click", () => {
        const current = root.getAttribute("data-bs-theme") || "light";
        applyTheme(current === "dark" ? "light" : "dark");
    });

    mediaQuery.addEventListener("change", () => {
        if (getMode() === "system") {
            applyTheme("system");
        }
    });

    applyTheme(getMode());
});