# robotframework-dashboard-hub

`robotdashboardhub`: one HTML overview page across several robotframework-dashboard databases and servers. Read the README first; it is the user documentation.

## Layout

| File | Role |
|---|---|
| `src/robotframework_dashboard_hub/cli.py` | the command line |
| `sources.py` | `Source`, the sources file, merging |
| `collect.py` | reads each source (database or `GET /get-run-stats`), never raises for a broken source |
| `generator.py` | fills `templates/hub.html`; bundles `js/` and `css/` with robotdashboard's `DependencyProcessor` |
| `compat.py` | **the only module that imports robotframework_dashboard** |
| `js/` | browser code; `stats.js` holds the pure calculations, `main.js` is the entry. Modules are concatenated into one script, so top-level names must be unique across files |

## Rules

- Everything used from robotframework-dashboard goes through `compat.py`. Its counterpart is the `hub-contract` skill in robotframework-dashboard (`../robotframework-dashboard/.claude/skills/hub-contract/SKILL.md`): when the hub starts using something new from robotdashboard, add it to that table too.
- Values from a server are untrusted: `collect._clean_runs` keeps only known fields with their types, and the page sets them as text (`textContent`), links only through `is_safe_url`.
- Validate a frontend change by generating a page (`robotdashboardhub -s <db> -n results/hub.html`) and opening it in light and dark mode.
- Checks: `ruff check . && ruff format --check . && mypy && pytest`, using `.venv` (see README, Development).
- Commit only when asked. Releases follow the `release` skill.
