"""AI Capital — Dash 52.

Served from the Launch Center hub on 4720 (primary). Optional alias port 8502
uses the same stack: /dash52 command center + /content-studio tools.
"""
from __future__ import annotations

import os

# Optional alias port when importing this package as an app entry.
os.environ.setdefault("HUB_PORT", "8502")
os.environ.setdefault("ORG_DATA_DIR", os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data_dash52"))

from app_launch_center.hub import app  # noqa: E402

__all__ = ["app"]
