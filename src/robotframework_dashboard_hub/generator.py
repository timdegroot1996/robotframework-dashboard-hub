"""Writes the hub page: one self-contained HTML file, bundled the way robotdashboard bundles its dashboard."""

from __future__ import annotations

import json
import zlib
from base64 import b64encode
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from .collect import SourceResult
from .compat import dependency_processor
from .version import __version__

PACKAGE_ROOT = Path(__file__).parent
TEMPLATE = PACKAGE_ROOT / "templates" / "hub.html"
# names from robotframework_dashboard.dependencies.DEPENDENCIES: CDN links, or the offline copies it ships
HUB_DEPENDENCIES = ("bootstrap_css", "datatables_css", "chartjs", "bootstrap_js", "datatables_js")
DEFAULT_TITLE = "RobotDashboard Hub"


def generate_hub(
    results: list[SourceResult],
    output_path: str | Path = "robot_dashboard_hub.html",
    title: str = "",
    offline: bool = False,
    generated: datetime | None = None,
) -> Path:
    title = title.strip() or DEFAULT_TITLE
    generated = generated or datetime.now().astimezone()
    bundler = dependency_processor(str(PACKAGE_ROOT / "js"), str(PACKAGE_ROOT / "css"), HUB_DEPENDENCIES)
    payload = {
        "title": title,
        "generated": generated.isoformat(timespec="seconds"),
        "version": __version__,
        "sources": [result.to_payload() for result in results],
    }
    html = TEMPLATE.read_text(encoding="utf-8")
    # the payload goes last: it is base64, so it cannot contain another placeholder
    for placeholder, value in (
        ("<!-- placeholder_dependencies -->", bundler.get_dependencies_block(offline)),
        ("<!-- placeholder_css -->", bundler.get_css_block()),
        ("<!-- placeholder_javascript -->", bundler.get_js_block()),
        ("placeholder_hub_title", escape(title)),
        ('"placeholder_hub_data"', f'"{compress_and_encode(payload)}"'),
    ):
        html = html.replace(placeholder, value)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def compress_and_encode(data: Any) -> str:
    """JSON, zlib, base64: the format js/data.js inflates with the browser's DecompressionStream"""
    return b64encode(zlib.compress(json.dumps(data).encode("utf-8"))).decode("ascii")
