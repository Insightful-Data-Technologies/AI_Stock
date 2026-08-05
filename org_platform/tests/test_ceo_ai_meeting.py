"""CEO AI meeting page — no red UI, green screen-share arrow."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path))
    from org_platform.store import platform as platform_mod
    from org_platform.api import app as app_mod

    platform_mod.rebind(str(tmp_path))
    return TestClient(app_mod.app)


def test_ceo_ai_meeting_no_red_has_green_arrow(client):
    page = client.get("/ceo-ai-meeting.html")
    assert page.status_code == 200
    html = page.text
    assert "green-arrow" in html
    assert "SEEING SHARE" in html or "share-banner" in html
    assert "ceo-chanan.png" in html
    assert "Hold to talk" in html or "השיחה חיה" in html
    assert "transcript" in html
    assert "LISTENING" in html
    assert "continuous" in html or "שיחה חיה" in html or "רציפה" in html
    # No hard-coded red palette in the page styles
    assert not re.search(r"--[a-z-]+:\s*#(f00|ff0000|e11|b45555|ff7b7b)\b", html, re.I)
    assert "#ff7b7b" not in html.lower()
    assert "LLM fallback" not in html  # removed scary fallback banner
