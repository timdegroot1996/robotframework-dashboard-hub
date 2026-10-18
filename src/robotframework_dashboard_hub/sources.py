"""Hub sources: robotdashboard databases (a file path) and robotdashboard servers (an http(s) URL).

A sources file adds a label, a link to the project's own dashboard and a group to each source::

    {
      "sources": [
        {"source": "team_a/robot_results.db", "label": "Team A", "dashboard_url": "https://ci.example.com/team_a.html"},
        {"source": "http://dashboards.example.com:8543", "label": "Webshop", "group": "Web"}
      ]
    }

Database paths in a sources file are relative to the folder of that file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

SourceType = Literal["db", "url"]
FIELDS = ("source", "label", "dashboard_url", "group")


class SourcesFileError(ValueError):
    """The sources file cannot be read or does not have the expected shape"""


@dataclass(frozen=True)
class Source:
    source: str
    type: SourceType
    label: str
    dashboard_url: str = ""
    group: str = ""

    @classmethod
    def from_value(
        cls, value: str, label: str = "", dashboard_url: str = "", group: str = "", base: Path | None = None
    ) -> Source:
        """A source from a database path or a server URL; a relative path is resolved against base"""
        value = value.strip()
        if not value:
            raise ValueError("a source cannot be empty")
        if _is_url(value):
            source_type: SourceType = "url"
            value = value.rstrip("/")
        elif "://" in value:
            raise ValueError(f"'{value}' is not a database path and not an http(s) URL")
        else:
            source_type = "db"
            if base is not None and not Path(value).is_absolute():
                value = str(base / value)
        if dashboard_url and not _is_url(dashboard_url):
            raise ValueError(f"dashboard_url '{dashboard_url}' of '{value}' must be an http(s) URL")
        return cls(
            source=value,
            type=source_type,
            label=label.strip() or default_label(value, source_type),
            dashboard_url=dashboard_url or (value if source_type == "url" else ""),
            group=group.strip(),
        )

    @property
    def key(self) -> str:
        """What makes two sources the same source"""
        if self.type == "url":
            return self.source.lower()
        return str(Path(self.source).resolve()).lower()


def default_label(value: str, source_type: SourceType) -> str:
    """host:port for a server, the file name without extension for a database"""
    if source_type == "url":
        return urlsplit(value).netloc or value
    return Path(value).stem or value


def load_sources_file(path: str | Path) -> list[Source]:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SourcesFileError(f"cannot read sources file '{path}': {error}") from error
    except json.JSONDecodeError as error:
        raise SourcesFileError(f"sources file '{path}' is not valid JSON: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise SourcesFileError(f"sources file '{path}' must be an object with a 'sources' list")
    sources = []
    for index, entry in enumerate(data["sources"]):
        sources.append(_source_from_entry(entry, index, path))
    return sources


def _source_from_entry(entry: Any, index: int, path: Path) -> Source:
    where = f"sources file '{path}', entry {index}"
    if isinstance(entry, str):
        entry = {"source": entry}
    if not isinstance(entry, dict):
        raise SourcesFileError(f"{where}: must be a string or an object")
    unknown = sorted(set(entry) - set(FIELDS))
    if unknown:
        raise SourcesFileError(f"{where}: unknown field(s) {', '.join(unknown)}, expected {', '.join(FIELDS)}")
    if not all(isinstance(entry.get(field, ""), str) for field in FIELDS):
        raise SourcesFileError(f"{where}: every field must be a string")
    try:
        return Source.from_value(
            entry.get("source", ""),
            label=entry.get("label", ""),
            dashboard_url=entry.get("dashboard_url", ""),
            group=entry.get("group", ""),
            base=path.parent,
        )
    except ValueError as error:
        raise SourcesFileError(f"{where}: {error}") from error


def merge_sources(*source_lists: list[Source]) -> list[Source]:
    """All sources in order, once each; a later duplicate only fills in what the first one left empty"""
    merged: dict[str, Source] = {}
    for sources in source_lists:
        for source in sources:
            first = merged.get(source.key)
            if first is None:
                merged[source.key] = source
                continue
            first_set, later_set = _explicit_fields(first), _explicit_fields(source)
            fill = {name: value for name, value in later_set.items() if name not in first_set}
            merged[source.key] = replace(
                first,
                label=fill.get("label", first.label),
                dashboard_url=fill.get("dashboard_url", first.dashboard_url),
                group=fill.get("group", first.group),
            )
    return list(merged.values())


def _explicit_fields(source: Source) -> dict[str, str]:
    """The fields that were given, not filled in by default"""
    defaults = Source.from_value(source.source)
    return {
        name: getattr(source, name)
        for name in ("label", "dashboard_url", "group")
        if getattr(source, name) != getattr(defaults, name)
    }


def _is_url(value: str) -> bool:
    parts = urlsplit(value)
    return parts.scheme in ("http", "https") and bool(parts.netloc)
