# robotframework-dashboard-hub

One overview page across several [robotframework-dashboard](https://github.com/MarketSquare/robotframework-dashboard)
databases and servers. Teams that keep one dashboard per project get a single page with the pass rate, run count
and duration of every project side by side, which projects failed last, which sources are down, and a link to
each project's own dashboard.

Like robotdashboard it writes one self-contained HTML file: no server needed to view it.

Requires Python 3.10 or newer and a robotframework-dashboard with `get_run_stats` (the release after 2.5.0).
Status: alpha.

```
pip install robotframework-dashboard-hub
robotdashboardhub -s team_a/robot_results.db -s team_b/robot_results.db           # databases
robotdashboardhub -s http://dashboards.example.com:8543 -s https://ci.example.com/rd # robotdashboard servers
robotdashboardhub --sourcesfile hub_sources.json -n hub.html -t "Nightly runs"
```

## Sources

A source is a robotdashboard database (the path of its `.db` file) or a robotdashboard server started with
`robotdashboard --server` (its `http://` or `https://` address).

- **Databases** are read with robotdashboard's own `DatabaseProcessor`, so a database of an older robotdashboard is
  migrated in place, the same as when robotdashboard opens it. A path that does not exist is reported, never created.
- **Servers** are asked for `GET /get-run-stats`, which needs no login (like `/get-outputs`). A server without that
  endpoint runs a robotdashboard that is too old, and is reported as such.

A source that is down or broken is shown as such on the page and in the console; the hub page is still written.
Servers are asked at the same time, each with `--timeout` seconds (default 10).

### Sources file

`--sourcesfile` adds a label, a link to the project's own dashboard and a group to each source. Database paths
in the file are relative to the folder of the file. An entry can also be just the source as a string.

```json
{
  "sources": [
    {"source": "team_a/robot_results.db", "label": "Team A", "dashboard_url": "https://ci.example.com/team_a.html", "group": "Web"},
    {"source": "http://dashboards.example.com:8543", "label": "Webshop API", "group": "Web"},
    "team_c/robot_results.db"
  ]
}
```

| Field | Default |
|---|---|
| `source` | required: database path or server URL |
| `label` | the file name without `.db`, or `host:port` of a server |
| `dashboard_url` | the server URL for a server; none for a database (the table then has no link) |
| `group` | none |

`-s` and `--sourcesfile` can be combined; a source given twice is used once, the sources file wins for its fields.

## The page

- **Tiles**: number of projects and runs, the pass rate of the latest run of every project, and sources down.
- **Pass rate trend**: passed tests out of all tests of all runs, per day or per week.
- **Latest run per project**: passed, failed and skipped tests of each project's latest run.
- **Average duration per project**.
- **Projects table**: status and counts of the latest run, pass rate, the share of the last 10 runs that failed
  (sorted worst first), average duration, number of runs and the link to the project's dashboard.
- **Sources table**: every source with its status, run count, robotdashboard version and what went wrong.

A project is what robotdashboard's overview page calls a project: by default one per run name within a source. When
runs have `project_` tags, *Projects by* switches to one project per tag (runs without one stay with their run name).
Light and dark mode follow the browser until you pick one.

## Command line

```
robotdashboardhub [-s SOURCE]... [--sourcesfile FILE] [-n NAME] [-t TITLE] [--offlinedependencies] [--timeout SECONDS]
```

| Option | |
|---|---|
| `-s`, `--source` | a database path or server URL, repeatable |
| `--sourcesfile` | JSON sources file, see above |
| `-n`, `--namehub` | the HTML file to write, default `robot_dashboard_hub.html` |
| `-t`, `--hubtitle` | page title, default `RobotDashboard Hub` |
| `--offlinedependencies` | inline Chart.js, Bootstrap and DataTables (robotdashboard's offline copies) instead of loading them from a CDN |
| `--timeout` | seconds to wait for each server, default 10 |
| `-v`, `--version` | |

## Python API

```python
from robotframework_dashboard_hub import Source, collect_all, generate_hub, load_sources_file, merge_sources

sources = merge_sources(load_sources_file("hub_sources.json"), [Source.from_value("extra/robot_results.db")])
results = collect_all(sources)  # SourceResult: status "ok", "unreachable" or "error", message, version, runs
generate_hub(results, "robot_dashboard_hub.html", title="Nightly runs", offline=False)
```

## Development

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ../robotframework-dashboard -e .[dev]    # Linux/macOS: .venv/bin/python
ruff check . && ruff format --check . && mypy
pytest
```

The tests build real robotdashboard databases by running a small suite with Robot Framework and the robotdashboard
command line, and run one test against a real `robotdashboard --server`.

Everything the hub uses from robotframework-dashboard is imported in `compat.py`. robotframework-dashboard has a
`hub-contract` skill that lists those parts, so a change there is checked against the hub first.

## Licence

MIT
