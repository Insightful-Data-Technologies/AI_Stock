"""AI Capital — Dash 52.

Claude's earlier split left Content Studio with a 'Not yet migrated' stub.
This package serves the completed Dash 52 shell on port 8502 using the same
Launch Center + Content Studio stack (Writing, Translate, Articles, Create Text,
MD, Image, Canva, Keyboard Fix).
"""
from __future__ import annotations

import os

# Prefer Dash 52 port unless already set by the runner.
os.environ.setdefault("HUB_PORT", "8502")
os.environ.setdefault("ORG_DATA_DIR", os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data_dash52"))

from app_launch_center.hub import app  # noqa: E402

__all__ = ["app"]
