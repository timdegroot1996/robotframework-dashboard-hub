import json
from pathlib import Path

import pytest

from robotframework_dashboard_hub import __version__
from robotframework_dashboard_hub.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"robotdashboardhub {__version__}"


def test_no_sources(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == 2
    assert "no sources" in capsys.readouterr().err


def test_invalid_source(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["-s", "ftp://host/x.db"])
    assert "not a database path and not an http" in capsys.readouterr().err


def test_invalid_sources_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "hub_sources.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        main(["--sourcesfile", str(path)])
    assert "must be an object with a 'sources' list" in capsys.readouterr().err


def test_generates_the_hub(databases: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sources_file = tmp_path / "hub_sources.json"
    sources_file.write_text(json.dumps({"sources": [{"source": str(databases["shop"]), "label": "Web"}]}), "utf-8")
    output = tmp_path / "hub.html"
    code = main(
        [
            "--sourcesfile",
            str(sources_file),
            "-s",
            str(databases["api"]),
            "-s",
            str(tmp_path / "gone.db"),
            "-n",
            str(output),
        ]
    )
    assert code == 0
    assert output.is_file()
    out = capsys.readouterr().out
    assert "Collecting 3 source(s)" in out
    assert "ok           Web: 2 runs" in out
    assert "ok           Api: 1 runs" in out
    assert "error        gone: database" in out
