import json
from pathlib import Path

import pytest

from robotframework_dashboard_hub.sources import Source, SourcesFileError, load_sources_file, merge_sources


def test_database_source_defaults() -> None:
    source = Source.from_value("teams/web/robot_results.db")
    assert source.type == "db"
    assert source.label == "robot_results"
    assert source.dashboard_url == ""
    assert source.group == ""


def test_url_source_defaults() -> None:
    source = Source.from_value("http://dashboards.example.com:8543/")
    assert source.type == "url"
    assert source.source == "http://dashboards.example.com:8543"
    assert source.label == "dashboards.example.com:8543"
    assert source.dashboard_url == "http://dashboards.example.com:8543"


@pytest.mark.parametrize("value", ["ftp://host/db", "javascript://alert(1)", "file:///tmp/x.db"])
def test_other_schemes_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="not a database path and not an http"):
        Source.from_value(value)


def test_empty_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Source.from_value("  ")


def test_dashboard_url_must_be_http() -> None:
    with pytest.raises(ValueError, match="must be an http"):
        Source.from_value("a.db", dashboard_url="javascript:alert(1)")


def write_sources(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_sources_file(tmp_path: Path) -> None:
    path = write_sources(
        tmp_path / "hub_sources.json",
        {
            "sources": [
                {
                    "source": "web/robot_results.db",
                    "label": "Web",
                    "group": "Shop",
                    "dashboard_url": "https://ci/web.html",
                },
                "http://api.example.com:8543",
            ]
        },
    )
    web, api = load_sources_file(path)
    # relative to the folder of the sources file, not the working directory
    assert Path(web.source) == tmp_path / "web" / "robot_results.db"
    assert (web.label, web.group, web.dashboard_url) == ("Web", "Shop", "https://ci/web.html")
    assert api.type == "url"
    assert api.label == "api.example.com:8543"


@pytest.mark.parametrize(
    "content, message",
    [
        ("{not json", "not valid JSON"),
        ("[]", "must be an object with a 'sources' list"),
        ('{"sources": {}}', "must be an object with a 'sources' list"),
        ('{"sources": [42]}', "entry 0: must be a string or an object"),
        ('{"sources": [{"source": "a.db", "colour": "red"}]}', "entry 0: unknown field\\(s\\) colour"),
        ('{"sources": [{"source": "a.db", "label": 3}]}', "entry 0: every field must be a string"),
        ('{"sources": [{"label": "no source"}]}', "entry 0: a source cannot be empty"),
    ],
)
def test_invalid_sources_file(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "hub_sources.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SourcesFileError, match=message):
        load_sources_file(path)


def test_missing_sources_file(tmp_path: Path) -> None:
    with pytest.raises(SourcesFileError, match="cannot read sources file"):
        load_sources_file(tmp_path / "nope.json")


def test_merge_keeps_order_and_drops_duplicates(tmp_path: Path) -> None:
    labelled = Source.from_value(str(tmp_path / "a.db"), label="Team A")
    same_without_label = Source.from_value(str(tmp_path / "a.db"), group="Web")
    other = Source.from_value("http://b:1")
    merged = merge_sources([labelled, other], [same_without_label, Source.from_value("HTTP://B:1/")])
    assert [source.label for source in merged] == ["Team A", "b:1"]
    # the duplicate fills in what the first one left empty
    assert merged[0].group == "Web"
