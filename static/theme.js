const themeButton = document.getElementById("theme-toggle");
const savedTheme = localStorage.getItem("studentHubTheme");

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;

    if (themeButton) {
        const isDark = theme === "dark";

        themeButton.textContent = isDark
            ? "☀️ Light mode"
            : "🌙 Dark mode";

        themeButton.setAttribute("aria-pressed", String(isDark));
    }
}

applyTheme(savedTheme === "dark" ? "dark" : "light");

if (themeButton) {
    themeButton.addEventListener("click", function () {
        const currentTheme = document.documentElement.dataset.theme;
        const nextTheme = currentTheme === "dark" ? "light" : "dark";

        localStorage.setItem("studentHubTheme", nextTheme);
        applyTheme(nextTheme);
    });
}