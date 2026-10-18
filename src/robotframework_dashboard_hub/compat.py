"""The robotframework-dashboard parts the hub uses, with one clear error when the installed version is too old."""

from __future__ import annotations

from typing import Any

MINIMUM = "the robotframework-dashboard release with get_run_stats (after 2.5.0)"

try:
    from robotframework_dashboard.database import DatabaseProcessor
    from robotframework_dashboard.dependencies import JS_ROOT, DependencyProcessor  # noqa: F401
    from robotframework_dashboard.version import __version__ as dashboard_version
except ImportError as error:  # pragma: no cover - depends on the installed dashboard
    raise ImportError(f"robotframework-dashboard-hub needs {MINIMUM}: {error}") from error

if not hasattr(DatabaseProcessor, "get_run_stats"):  # pragma: no cover - depends on the installed dashboard
    raise ImportError(f"robotframework-dashboard-hub needs {MINIMUM}, found {dashboard_version}")


def dashboard_version_number() -> str:
    """The installed robotframework-dashboard version without the 'Robotdashboard ' prefix it carries"""
    return str(dashboard_version).split()[-1]


def read_run_stats(database_path: str) -> list[dict[str, Any]]:
    """Run statistics of a robotdashboard SQLite database, read the way robotdashboard reads it.
    Opening migrates an older schema in place, exactly like robotdashboard itself does."""
    database = DatabaseProcessor(database_path)
    database.open_database()
    try:
        stats: list[dict[str, Any]] = database.get_run_stats()
    finally:
        database.close_database()
    return stats


def dependency_processor(js_root: str, css_root: str, dependencies: tuple[str, ...]) -> Any:
    """robotdashboard's bundler, pointed at the hub's own js/ and css/ folders"""
    return DependencyProcessor(js_root=js_root, css_root=css_root, dependencies=dependencies, exclude=())
