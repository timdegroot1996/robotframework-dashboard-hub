// Pure functions from the payload to what the page shows; no DOM, so they can be unit tested.

const RECENT_RUNS = 10;

// the run tags that make a project, like robotdashboard's overview page
function project_tags(run) {
    return (run.tags || []).filter(tag => tag.toLowerCase().startsWith("project_"));
}

// projects of every reachable source. mode "name": one project per run name (robotdashboard's overview default).
// mode "tag": one project per project_ tag; a run without one stays in the project of its run name, so no
// run disappears from the hub. Runs keep their order, oldest first.
function group_projects(sources, mode = "name") {
    const projects = [];
    sources.forEach((source, sourceIndex) => {
        if (source.status !== "ok") return;
        const byName = new Map();
        for (const run of source.runs) {
            const tags = mode === "tag" ? project_tags(run) : [];
            const names = tags.length ? tags : [run.name || "(no name)"];
            for (const name of names) {
                if (!byName.has(name)) byName.set(name, []);
                byName.get(name).push(run);
            }
        }
        for (const [name, runs] of byName) {
            projects.push({ id: `${sourceIndex}:${name}`, name, source, runs });
        }
    });
    return projects;
}

function has_project_tags(sources) {
    return sources.some(source => source.runs.some(run => project_tags(run).length > 0));
}

// the name shown in graphs: the source label alone when the source is one project
function project_label(project, projects) {
    const siblings = projects.filter(other => other.source === project.source);
    return siblings.length === 1 ? project.source.label : `${project.source.label} · ${project.name}`;
}

function latest_run(project) {
    return project.runs.length ? project.runs[project.runs.length - 1] : null;
}

// percentage of passed tests, null without tests
function pass_rate(passed, total) {
    return total > 0 ? (passed / total) * 100 : null;
}

// same status rule as robotdashboard: any failure fails, only skipped tests is skipped
function run_status(run) {
    if (!run) return "none";
    if (run.failed > 0) return "failed";
    if (run.skipped > 0 && run.passed === 0) return "skipped";
    return "passed";
}

// percentage of the last RECENT_RUNS runs that failed
function recent_fail_rate(project) {
    const recent = project.runs.slice(-RECENT_RUNS);
    if (!recent.length) return null;
    return (recent.filter(run => run_status(run) === "failed").length / recent.length) * 100;
}

function average_duration(project) {
    if (!project.runs.length) return null;
    return project.runs.reduce((sum, run) => sum + run.elapsed_s, 0) / project.runs.length;
}

function summary(sources, projects) {
    let passed = 0;
    let total = 0;
    for (const project of projects) {
        const run = latest_run(project);
        if (run) {
            passed += run.passed;
            total += run.total;
        }
    }
    return {
        projects: projects.length,
        // counted per source: in "tag" mode one run can be in more than one project
        runs: sources.reduce((sum, source) => sum + (source.status === "ok" ? source.runs.length : 0), 0),
        passRate: pass_rate(passed, total),
        sourcesDown: sources.filter(source => source.status !== "ok").length,
        sources: sources.length,
    };
}

// "2026-08-17" of a run, from start_time (local time of the run) or run_start
function run_day(run) {
    return String(run.start_time || run.run_start).slice(0, 10);
}

// the Monday of the ISO week of a "YYYY-MM-DD" day
function week_start(day) {
    const date = new Date(`${day}T00:00:00Z`);
    const weekday = (date.getUTCDay() + 6) % 7;
    date.setUTCDate(date.getUTCDate() - weekday);
    return date.toISOString().slice(0, 10);
}

// pass rate of all tests of all sources per day or week, oldest first; every run counts once
function pass_rate_trend(sources, period = "daily") {
    const buckets = new Map();
    for (const source of sources) {
        if (source.status !== "ok") continue;
        for (const run of source.runs) {
            const day = run_day(run);
            if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) continue;
            const key = period === "weekly" ? week_start(day) : day;
            const bucket = buckets.get(key) || { passed: 0, total: 0, runs: 0 };
            bucket.passed += run.passed;
            bucket.total += run.total;
            bucket.runs += 1;
            buckets.set(key, bucket);
        }
    }
    const labels = [...buckets.keys()].sort();
    return {
        labels,
        values: labels.map(key => pass_rate(buckets.get(key).passed, buckets.get(key).total)),
        runs: labels.map(key => buckets.get(key).runs),
    };
}

// 12.3s, 4m 5s, 1h 2m
function format_duration(seconds) {
    if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "-";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}

function format_percentage(value) {
    return value === null || value === undefined ? "-" : `${value.toFixed(1)}%`;
}

export {
    group_projects,
    has_project_tags,
    project_label,
    latest_run,
    pass_rate,
    run_status,
    recent_fail_rate,
    average_duration,
    summary,
    run_day,
    week_start,
    pass_rate_trend,
    format_duration,
    format_percentage,
};
