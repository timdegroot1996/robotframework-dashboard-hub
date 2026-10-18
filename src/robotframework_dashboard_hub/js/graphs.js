import { css_color } from "./theme.js";
import {
    project_label,
    latest_run,
    pass_rate_trend,
    average_duration,
    format_duration,
    format_percentage,
} from "./stats.js";

const hubGraphs = {};

function replace_graph(id, config) {
    if (hubGraphs[id]) hubGraphs[id].destroy();
    hubGraphs[id] = new Chart(document.getElementById(id), config);
}

function create_trend_graph(sources, period) {
    const trend = pass_rate_trend(sources, period);
    replace_graph("trendGraph", {
        type: "line",
        data: {
            labels: trend.labels,
            datasets: [{
                label: "Pass rate",
                data: trend.values,
                borderColor: css_color("--color-passed"),
                backgroundColor: css_color("--color-passed"),
                tension: 0.2,
                spanGaps: true,
            }],
        },
        options: {
            maintainAspectRatio: false,
            scales: { y: { min: 0, max: 100, ticks: { callback: value => `${value}%` } } },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => `${format_percentage(context.parsed.y)} of tests passed, ${trend.runs[context.dataIndex]} run(s)`,
                    },
                },
            },
        },
    });
}

function create_latest_graph(projects) {
    const labels = projects.map(project => project_label(project, projects));
    const latest = projects.map(latest_run);
    const dataset = (label, key, color) => ({
        label,
        data: latest.map(run => (run ? run[key] : 0)),
        backgroundColor: css_color(color),
    });
    replace_graph("latestGraph", {
        type: "bar",
        data: {
            labels,
            datasets: [
                dataset("Passed", "passed", "--color-passed"),
                dataset("Failed", "failed", "--color-failed"),
                dataset("Skipped", "skipped", "--color-skipped"),
            ],
        },
        options: {
            maintainAspectRatio: false,
            indexAxis: "y",
            scales: { x: { stacked: true, title: { display: true, text: "tests" } }, y: { stacked: true } },
        },
    });
}

function create_duration_graph(projects) {
    replace_graph("durationGraph", {
        type: "bar",
        data: {
            labels: projects.map(project => project_label(project, projects)),
            datasets: [{
                label: "Average duration",
                data: projects.map(average_duration),
                backgroundColor: css_color("--color-highlight"),
            }],
        },
        options: {
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { callback: value => format_duration(value) } } },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => format_duration(context.parsed.y) } },
            },
        },
    });
}

export {
    create_trend_graph,
    create_latest_graph,
    create_duration_graph,
};
