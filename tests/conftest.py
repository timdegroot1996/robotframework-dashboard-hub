"""Fixtures: real robotdashboard databases, built from a small suite through robot and the robotdashboard CLI,
and a stub server for the URL sources."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from robot import run

SUITE = """\
*** Test Cases ***
Passes
    Log    ok
Fails
    Fail    on purpose
Skips
    Skip    not today
"""


def make_database(folder: Path, name: str, runs: int, tags: str = "") -> Path:
    """A robotdashboard database with `runs` runs of a suite named `name`: 1 passed, 1 failed, 1 skipped each"""
    folder.mkdir(parents=True, exist_ok=True)
    suite = folder / f"{name}.robot"
    suite.write_text(SUITE, encoding="utf-8")
    database = folder / f"{name}.db"
    for index in range(runs):
        output = f"output-{name}-{index}.xml"
        run(str(suite), output=str(folder / output), log="NONE", report="NONE", console="none")
        # relative names: '-o' splits tags off on ':', which a Windows drive letter also has
        command = [sys.executable, "-m", "robotframework_dashboard.main", "-o", f"{output}:{tags}" if tags else output]
        command += ["-d", database.name, "-g", "false"]
        subprocess.run(command, check=True, capture_output=True, cwd=folder)
    return database


@pytest.fixture(scope="session")
def databases(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    folder = tmp_path_factory.mktemp("databases")
    return {
        "shop": make_database(folder, "Shop", runs=2, tags="nightly:project_web"),
        "api": make_database(folder, "Api", runs=1),
    }


class StubServer:
    """Answers GET /get-run-stats with whatever the test sets"""

    def __init__(self) -> None:
        self.status = 200
        self.body: bytes = b""
        self.requests: list[str] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                stub.requests.append(self.path)
                self.send_response(stub.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(stub.body)

            def log_message(self, *args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def answer(self, data: Any, status: int = 200) -> None:
        self.status = status
        self.body = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")


@pytest.fixture
def stub_server() -> Iterator[StubServer]:
    stub = StubServer()
    yield stub
    stub.server.shutdown()
    stub.server.server_close()
