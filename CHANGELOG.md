# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## Unreleased

### Added
- `robotdashboardhub`: one self-contained HTML page across several robotframework-dashboard databases (`-s path.db`) and servers (`-s http://host:port`, read through `GET /get-run-stats`)
- Sources file (`--sourcesfile`) with a `label`, `dashboard_url` and `group` per source
- Tiles, pass rate trend per day or week, latest run per project, average duration per project, a projects table and a sources table; projects by run name or by `project_` tag, like robotdashboard's overview page
- A source that is down or broken is reported on the page and in the console without stopping the others
- `--offlinedependencies` uses robotdashboard's offline copies of Chart.js, Bootstrap and DataTables
