"""Read the run statistics of every source. A source that is down or broken is reported, never fatal."""

from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .compat import dashboard_version_number, read_run_stats
from .sources import Source
from .version import __version__

Status = Literal["ok", "unreachable", "error"]
ENDPOINT = "/get-run-stats"
# a server answers with every run it has; this only guards against a source that never stops sending
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
INT_FIELDS = ("total", "passed", "failed", "skipped")
STR_FIELDS = ("run_start", "name", "run_alias", "start_time", "project_version")
LIST_FIELDS = ("tags", "metadata")


@dataclass
class SourceResult:
    source: Source
    status: Status
    message: str = ""
    version: str = ""
    runs: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "source": self.source.source,
            "type": self.source.type,
            "label": self.source.label,
            "dashboard_url": self.source.dashboard_url,
            "group": self.source.group,
            "status": self.status,
            "message": self.message,
            "version": self.version,
            "runs": self.runs,
        }


def collect(source: Source, timeout: float = 10.0) -> SourceResult:
    if source.type == "db":
        return _collect_db(source)
    return _collect_url(source, timeout)


def collect_all(sources: list[Source], timeout: float = 10.0) -> list[SourceResult]:
    """Every source in order; servers are asked at the same time so one slow server does not add up"""
    if not sources:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(sources))) as pool:
        return list(pool.map(lambda source: collect(source, timeout), sources))


def _collect_db(source: Source) -> SourceResult:
    # DatabaseProcessor creates a missing database, the hub must not
    if not Path(source.source).is_file():
        return SourceResult(source, "error", f"database '{source.source}' not found")
    try:
        runs = read_run_stats(source.source)
    except sqlite3.Error as error:
        return SourceResult(source, "error", f"cannot read database '{source.source}': {error}")
    return SourceResult(source, "ok", version=dashboard_version_number(), runs=_clean_runs(runs))


def _collect_url(source: Source, timeout: float) -> SourceResult:
    url = source.source + ENDPOINT
    request = Request(url, headers={"Accept": "application/json", "User-Agent": f"robotdashboardhub/{__version__}"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        if error.code == 404:
            message = f"{url} not found: the server runs a robotframework-dashboard without {ENDPOINT}"
        else:
            message = f"{url} answered HTTP {error.code}: {_detail(error)}"
        return SourceResult(source, "error", message)
    except (URLError, TimeoutError, OSError) as error:
        reason = error.reason if isinstance(error, URLError) else error
        return SourceResult(source, "unreachable", f"cannot reach {url}: {reason}")
    if len(body) > MAX_RESPONSE_BYTES:
        return SourceResult(source, "error", f"{url} sent more than {MAX_RESPONSE_BYTES // (1024 * 1024)} MB")
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return SourceResult(source, "error", f"{url} did not answer with JSON")
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        return SourceResult(source, "error", f"{url} did not answer with {{version, runs}}")
    version = str(data.get("version", "")).split()[-1:] or [""]
    return SourceResult(source, "ok", version=version[0], runs=_clean_runs(data["runs"]))


def _detail(error: HTTPError) -> str:
    try:
        detail = json.loads(error.read()).get("detail", "")
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, OSError):
        detail = ""
    return str(detail) or str(error.reason)


def _clean_runs(runs: list[Any]) -> list[dict[str, Any]]:
    """Only the known fields, with their types, oldest first. A server is another program: a run that does not
    have the shape is left out instead of breaking the page"""
    cleaned = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        try:
            item: dict[str, Any] = {name: int(run.get(name) or 0) for name in INT_FIELDS}
            item["elapsed_s"] = float(run.get("elapsed_s") or 0)
        except (TypeError, ValueError):
            continue
        for name in STR_FIELDS:
            item[name] = str(run.get(name) or "")
        for name in LIST_FIELDS:
            value = run.get(name)
            item[name] = [str(entry) for entry in value] if isinstance(value, list) else []
        if not item["run_start"]:
            continue
        cleaned.append(item)
    cleaned.sort(key=lambda item: item["start_time"] or item["run_start"])
    return cleaned
