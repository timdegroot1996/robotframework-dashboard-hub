import base64
import json
import re
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from robotframework_dashboard_hub import __version__
from robotframework_dashboard_hub.collect import SourceResult, collect
from robotframework_dashboard_hub.generator import DEFAULT_TITLE, generate_hub
from robotframework_dashboard_hub.sources import Source


def payload_of(html: str) -> Any:
    match = re.search(r'const base64Str = "([A-Za-z0-9+/=]+)";', html)
    assert match, "no payload in the page"
    return json.loads(zlib.decompress(base64.b64decode(match.group(1))))


def test_hub_page(databases: dict[str, Path], tmp_path: Path) -> None:
    results = [
        collect(Source.from_value(str(databases["shop"]), label="Web shop", group="Web")),
        SourceResult(Source.from_value("http://down:1"), "unreachable", "cannot reach"),
    ]
    generated = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    output = generate_hub(results, tmp_path / "out" / "hub.html", title="Nightly <runs>", generated=generated)
    html = output.read_text(encoding="utf-8")
    assert "<title>Nightly &lt;runs&gt;</title>" in html
    assert "placeholder_" not in html.replace('"placeholder_")', "")
    payload = payload_of(html)
    assert payload["title"] == "Nightly <runs>"
    assert payload["generated"] == "2026-10-18T12:00:00+00:00"
    assert payload["version"] == __version__
    web, down = payload["sources"]
    assert (web["label"], web["group"], web["status"], len(web["runs"])) == ("Web shop", "Web", "ok", 2)
    assert (down["status"], down["message"], down["runs"]) == ("unreachable", "cannot reach", [])


def test_page_bundles_the_hub_modules(tmp_path: Path) -> None:
    html = generate_hub([], tmp_path / "hub.html").read_text(encoding="utf-8")
    assert f"<title>{DEFAULT_TITLE}</title>" in html
    for module in ("stats.js", "data.js", "graphs.js", "tables.js", "theme.js", "main.js"):
        assert f"// === {module} ===" in html
    # main.js runs last, after every module it uses
    assert html.index("// === main.js ===") > html.index("// === tables.js ===")
    script = html[html.index("// MERGED MODULES") :]
    assert not re.search(r"^\s*(import|export)\s", script, re.MULTILINE)
    assert "/* === hub.css === */" in html and "/* === colors.css === */" in html


def test_cdn_and_offline_dependencies(tmp_path: Path) -> None:
    online = generate_hub([], tmp_path / "online.html").read_text(encoding="utf-8")
    assert '<script src="https://cdn.jsdelivr.net/npm/chart.js' in online
    assert "gridstack" not in online
    offline = generate_hub([], tmp_path / "offline.html", offline=True).read_text(encoding="utf-8")
    assert "cdn.jsdelivr.net/npm/chart.js" not in offline
    assert "<!-- chartjs -->" in offline and "<!-- datatables_js -->" in offline
