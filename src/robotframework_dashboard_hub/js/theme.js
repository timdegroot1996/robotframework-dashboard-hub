// Light and dark mode, following robotframework-dashboard's theme.js: the browser preference until the
// user picks one, which is remembered per browser.
import { rflogoSVG, sunSVG, moonSVG, bugSVG, githubSVG, docsSVG } from "./svg.js";

const THEME_KEY = "robotdashboardhub-theme";

function stored_theme() {
    try {
        return localStorage.getItem(THEME_KEY);
    } catch {
        return null;
    }
}

function store_theme(theme) {
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch {
        // private window or blocked storage: the choice lasts until the page is closed
    }
}

function is_dark_mode() {
    return document.documentElement.classList.contains("dark-mode");
}

function setup_theme() {
    const theme = stored_theme();
    const dark = theme ? theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    apply_theme(dark);
}

function toggle_theme() {
    const dark = !is_dark_mode();
    store_theme(dark ? "dark" : "light");
    apply_theme(dark);
}

function apply_theme(dark) {
    const html = document.documentElement;
    html.classList.toggle("dark-mode", dark);
    html.setAttribute("data-bs-theme", dark ? "dark" : "light");
    const navigation = document.getElementById("navigation");
    navigation.classList.toggle("navbar-dark", dark);
    navigation.classList.toggle("navbar-light", !dark);
    const color = dark ? "white" : "black";
    document.getElementById("rflogo").innerHTML = rflogoSVG(color);
    document.getElementById("themeDark").innerHTML = sunSVG;
    document.getElementById("themeLight").innerHTML = moonSVG;
    document.getElementById("themeDark").hidden = !dark;
    document.getElementById("themeLight").hidden = dark;
    document.getElementById("docs").innerHTML = docsSVG(color);
    document.getElementById("bug").innerHTML = bugSVG(color);
    document.getElementById("github").innerHTML = githubSVG(color);
    Chart.defaults.color = dark ? "#eee" : "#666";
    Chart.defaults.borderColor = dark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)";
}

// a CSS color variable of the current theme, for Chart.js
function css_color(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export {
    setup_theme,
    toggle_theme,
    is_dark_mode,
    css_color,
};
