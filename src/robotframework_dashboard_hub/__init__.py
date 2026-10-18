"""One overview page across several robotframework-dashboard databases and servers.

Usage::

    robotdashboardhub -s team_a/robot_results.db -s http://dashboards.example.com:8543
    robotdashboardhub --sourcesfile hub_sources.json -n hub.html -t "Nightly runs"

Programs can collect and generate without the command line::

    from robotframework_dashboard_hub import Source, collect_all, generate_hub

    results = collect_all([Source.from_value("robot_results.db")])
    generate_hub(results, "robot_dashboard_hub.html")
"""

from .collect import SourceResult, collect, collect_all
from .generator import generate_hub
from .sources import Source, SourcesFileError, load_sources_file, merge_sources
from .version import __version__

__all__ = [
    "Source",
    "SourceResult",
    "SourcesFileError",
    "__version__",
    "collect",
    "collect_all",
    "generate_hub",
    "load_sources_file",
    "merge_sources",
]
