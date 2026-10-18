"""The hub against a real `robotdashboard --server`: the endpoint and fields the hub reads.
Skipped when robotframework-dashboard is installed without its server extra."""

import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

from robotframework_dashboard_hub.collect import collect
from robotframework_dashboard_hub.sources import Source

pytest.importorskip("fastapi_offline")
pytest.importorskip("uvicorn")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_robotdashboard_server_source(databases: dict[str, Path], tmp_path: Path) -> None:
    port = free_port()
    command = [sys.executable, "-m", "robotframework_dashboard.main", "--server", f"127.0.0.1:{port}"]
    command += ["-d", str(databases["shop"]), "-n", str(tmp_path / "dashboard.html")]
    server = subprocess.Popen(command, cwd=tmp_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                urlopen(f"{url}/get-outputs", timeout=1).close()
                break
            except OSError:
                if time.monotonic() > deadline or server.poll() is not None:
                    pytest.fail("robotdashboard --server did not start")
                time.sleep(0.2)
        result = collect(Source.from_value(url))
    finally:
        server.terminate()
        server.wait(timeout=10)
    assert result.status == "ok", result.message
    assert len(result.runs) == 2
    from_database = collect(Source.from_value(str(databases["shop"])))
    assert result.runs == from_database.runs
    assert result.version == from_database.version
