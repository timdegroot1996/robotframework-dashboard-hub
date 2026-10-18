from pathlib import Path

import pytest

from conftest import StubServer
from robotframework_dashboard_hub.collect import _clean_runs, collect, collect_all
from robotframework_dashboard_hub.compat import dashboard_version_number
from robotframework_dashboard_hub.sources import Source

RUN = {
    "run_start": "2026-08-17 02:15:12.070100+02:00",
    "name": "Shop",
    "run_alias": "a",
    "total": 3,
    "passed": 1,
    "failed": 1,
    "skipped": 1,
    "elapsed_s": 1.5,
    "start_time": "2026-08-17 02:15:12.070100",
    "tags": ["nightly"],
    "metadata": [],
    "project_version": "",
}


def test_database_source(databases: dict[str, Path]) -> None:
    result = collect(Source.from_value(str(databases["shop"])))
    assert result.status == "ok"
    assert result.version == dashboard_version_number()
    assert len(result.runs) == 2
    run = result.runs[0]
    assert (run["name"], run["total"], run["passed"], run["failed"], run["skipped"]) == ("Shop", 3, 1, 1, 1)
    assert run["tags"] == ["nightly", "project_web"]
    assert result.runs[0]["start_time"] <= result.runs[1]["start_time"]


def test_missing_database_is_reported_and_not_created(tmp_path: Path) -> None:
    path = tmp_path / "missing.db"
    result = collect(Source.from_value(str(path)))
    assert result.status == "error"
    assert "not found" in result.message
    assert not path.exists()


def test_broken_database_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "broken.db"
    path.write_bytes(b"this is not sqlite" * 100)
    result = collect(Source.from_value(str(path)))
    assert result.status == "error"
    assert "cannot read database" in result.message


def test_server_source(stub_server: StubServer) -> None:
    stub_server.answer({"version": "Robotdashboard 2.6.0", "runs": [RUN]})
    result = collect(Source.from_value(stub_server.url))
    assert result.status == "ok"
    assert result.version == "2.6.0"
    assert result.runs == [RUN]
    assert stub_server.requests == ["/get-run-stats"]


def test_server_without_endpoint(stub_server: StubServer) -> None:
    stub_server.answer({"detail": "Not Found"}, status=404)
    result = collect(Source.from_value(stub_server.url))
    assert result.status == "error"
    assert "without /get-run-stats" in result.message


def test_server_error_detail_is_shown(stub_server: StubServer) -> None:
    stub_server.answer({"detail": "get_run_stats is not implemented in the custom databaseclass"}, status=501)
    result = collect(Source.from_value(stub_server.url))
    assert result.status == "error"
    assert "HTTP 501: get_run_stats is not implemented" in result.message


@pytest.mark.parametrize(
    "body, message",
    [
        (b"<html>", "did not answer with JSON"),
        (b'{"runs": {}}', "did not answer with {version, runs}"),
        (b"[]", "{version, runs}"),
    ],
)
def test_server_with_unexpected_answer(stub_server: StubServer, body: bytes, message: str) -> None:
    stub_server.answer(body)
    result = collect(Source.from_value(stub_server.url))
    assert result.status == "error"
    assert message in result.message


def test_unreachable_server() -> None:
    result = collect(Source.from_value("http://127.0.0.1:9"), timeout=2)
    assert result.status == "unreachable"
    assert "cannot reach http://127.0.0.1:9/get-run-stats" in result.message


def test_runs_of_another_shape_are_left_out() -> None:
    runs = [
        "not a run",
        {**RUN, "total": "many"},
        {**RUN, "run_start": ""},
        {**RUN, "run_start": "2026-08-18 00:00:00", "start_time": "2026-08-18 00:00:00", "tags": "a,b", "extra": 1},
        RUN,
    ]
    cleaned = _clean_runs(runs)
    assert [run["run_start"] for run in cleaned] == [RUN["run_start"], "2026-08-18 00:00:00"]
    assert cleaned[1]["tags"] == []
    assert "extra" not in cleaned[1]


def test_collect_all_keeps_the_order(databases: dict[str, Path], stub_server: StubServer, tmp_path: Path) -> None:
    stub_server.answer({"version": "x", "runs": []})
    sources = [
        Source.from_value(stub_server.url),
        Source.from_value(str(tmp_path / "missing.db")),
        Source.from_value(str(databases["api"])),
    ]
    assert [result.source for result in collect_all(sources)] == sources
    assert collect_all([]) == []
