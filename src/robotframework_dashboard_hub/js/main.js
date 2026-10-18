import { hub, load_hub_data } from "./data.js";
import { setup_theme, toggle_theme } from "./theme.js";
import { group_projects, has_project_tags, summary, format_percentage } from "./stats.js";
import { create_trend_graph, create_latest_graph, create_duration_graph } from "./graphs.js";
import { create_projects_table, create_sources_table } from "./tables.js";

const view = { groupBy: "name", period: "daily" };

function render_summary(projects) {
    const totals = summary(hub.sources, projects);
    document.getElementById("tileProjects").textContent = totals.projects;
    document.getElementById("tileRuns").textContent = totals.runs;
    document.getElementById("tilePassRate").textContent = format_percentage(totals.passRate);
    document.getElementById("tileSourcesDown").textContent = `${totals.sourcesDown} / ${totals.sources}`;
}

function render_source_problems() {
    const down = hub.sources.filter(source => source.status !== "ok");
    const alert = document.getElementById("sourceProblems");
    alert.hidden = down.length === 0;
    alert.textContent = down.length === 0 ? "" : `Not included: ${down.map(source => `${source.label} (${source.message})`).join("; ")}`;
}

function render_graphs(projects) {
    create_trend_graph(hub.sources, view.period);
    create_latest_graph(projects);
    create_duration_graph(projects);
}

function render() {
    const projects = group_projects(hub.sources, view.groupBy);
    render_summary(projects);
    render_graphs(projects);
    create_projects_table(projects);
}

function setup_eventlisteners() {
    for (const id of ["themeDark", "themeLight"]) {
        document.getElementById(id).addEventListener("click", () => {
            toggle_theme();
            render_graphs(group_projects(hub.sources, view.groupBy));
        });
    }
    document.getElementById("groupBy").addEventListener("change", event => {
        view.groupBy = event.target.value;
        render();
    });
    document.querySelectorAll("input[name='trendPeriod']").forEach(input => {
        input.addEventListener("change", () => {
            view.period = input.value;
            create_trend_graph(hub.sources, view.period);
        });
    });
}

async function main() {
    await load_hub_data();
    setup_theme();
    document.getElementById("hubTitle").textContent = hub.title;
    document.getElementById("generatedInfo").textContent =
        `Generated ${hub.generated.replace("T", " ")} by robotdashboardhub ${hub.version}`;
    document.getElementById("groupByControl").hidden = !has_project_tags(hub.sources);
    Chart.defaults.font.size = 12;
    render_source_problems();
    create_sources_table(hub.sources);
    render();
    setup_eventlisteners();
}

main();
