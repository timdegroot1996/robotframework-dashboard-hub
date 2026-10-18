import { is_safe_url } from "./escape.js";
import {
    latest_run,
    pass_rate,
    run_status,
    recent_fail_rate,
    average_duration,
    format_duration,
    format_percentage,
} from "./stats.js";

const hubTables = {};

// every value from a source is set as text, never as HTML: a server is another program
function cell(text, sortValue) {
    const td = document.createElement("td");
    td.textContent = text;
    if (sortValue !== undefined) td.dataset.order = String(sortValue);
    return td;
}

function badge_cell(status, text = status) {
    const td = document.createElement("td");
    const span = document.createElement("span");
    span.className = `badge hub-status hub-status-${status}`;
    span.textContent = text;
    td.appendChild(span);
    return td;
}

function link_cell(url) {
    const td = document.createElement("td");
    if (url && is_safe_url(url)) {
        const link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = "Open";
        td.appendChild(link);
    } else {
        td.textContent = "-";
    }
    return td;
}

function fill_table(id, rows, options) {
    if (hubTables[id]) {
        hubTables[id].destroy();
        delete hubTables[id];
    }
    const tbody = document.querySelector(`#${id} tbody`);
    tbody.replaceChildren(...rows);
    hubTables[id] = new DataTable(`#${id}`, { paging: false, info: false, ...options });
}

function create_projects_table(projects) {
    const rows = projects.map(project => {
        const run = latest_run(project);
        const tr = document.createElement("tr");
        const rate = run ? pass_rate(run.passed, run.total) : null;
        const failRate = recent_fail_rate(project);
        const duration = average_duration(project);
        tr.append(
            cell(project.name),
            cell(project.source.label),
            cell(project.source.group || "-"),
            badge_cell(run_status(run)),
            cell(run ? (run.start_time || run.run_start).slice(0, 19) : "-"),
            cell(run ? run.passed : 0),
            cell(run ? run.failed : 0),
            cell(run ? run.skipped : 0),
            cell(format_percentage(rate), rate ?? -1),
            cell(format_percentage(failRate), failRate ?? -1),
            cell(format_duration(duration), duration ?? -1),
            cell(project.runs.length),
            link_cell(project.source.dashboard_url),
        );
        return tr;
    });
    // worst first: the highest recent fail rate
    fill_table("projectsTable", rows, { order: [[9, "desc"]] });
}

function create_sources_table(sources) {
    const rows = sources.map(source => {
        const tr = document.createElement("tr");
        if (source.status !== "ok") tr.classList.add("hub-source-down");
        tr.append(
            cell(source.label),
            cell(source.source),
            cell(source.group || "-"),
            badge_cell(source.status),
            cell(source.runs.length),
            cell(source.version || "-"),
            cell(source.message || ""),
        );
        return tr;
    });
    fill_table("sourcesTable", rows, { searching: false, ordering: false });
}

export {
    create_projects_table,
    create_sources_table,
};
