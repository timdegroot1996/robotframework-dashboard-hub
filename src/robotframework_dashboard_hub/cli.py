"""The ``robotdashboardhub`` command: collect every source and write the hub page."""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter

from .collect import collect_all
from .generator import DEFAULT_TITLE, generate_hub
from .sources import Source, SourcesFileError, load_sources_file, merge_sources
from .version import __version__

STATUS_WIDTH = len("unreachable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robotdashboardhub",
        description="One overview page across several robotframework-dashboard databases and servers.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-s",
        "--source",
        action="append",
        default=[],
        metavar="SOURCE",
        help="a robotdashboard database (path to the .db) or server (http(s)://host:port), repeatable",
    )
    parser.add_argument(
        "--sourcesfile",
        metavar="FILE",
        help="JSON file with sources and their label, dashboard_url and group, see the README",
    )
    parser.add_argument(
        "-n",
        "--namehub",
        default="robot_dashboard_hub.html",
        metavar="NAME",
        help="the HTML file to write (default robot_dashboard_hub.html)",
    )
    parser.add_argument("-t", "--hubtitle", default="", metavar="TITLE", help=f"page title (default {DEFAULT_TITLE})")
    parser.add_argument(
        "--offlinedependencies",
        action="store_true",
        help="inline Chart.js, Bootstrap and DataTables instead of loading them from a CDN",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        metavar="SECONDS",
        help="how long to wait for each server (default 10)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        file_sources = load_sources_file(args.sourcesfile) if args.sourcesfile else []
        cli_sources = [Source.from_value(value) for value in args.source]
    except (SourcesFileError, ValueError) as error:
        parser.error(str(error))
    sources = merge_sources(file_sources, cli_sources)
    if not sources:
        parser.error("no sources: give at least one -s/--source or a --sourcesfile")

    start = perf_counter()
    print(f"Collecting {len(sources)} source(s)")
    results = collect_all(sources, timeout=args.timeout)
    for result in results:
        detail = f"{len(result.runs)} runs" if result.status == "ok" else result.message
        print(f"  {result.status.ljust(STATUS_WIDTH)}  {result.source.label}: {detail}")
    output = generate_hub(results, args.namehub, title=args.hubtitle, offline=args.offlinedependencies)
    print(f"Created hub '{Path(output).resolve()}' in {perf_counter() - start:.2f} seconds")
    return 0
