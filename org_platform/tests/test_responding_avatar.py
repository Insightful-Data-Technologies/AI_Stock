"""Responding avatar + CEO portrait on Forecast 1:1 stage."""
from __future__ import annotations

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


def test_meeting_page_has_portrait_and_responding_avatar(client):
    page = client.get("/meeting/demo-id")
    assert page.status_code == 200
    html = page.text
    assert 'id="mePortrait"' in html
    assert "ceo-chanan.png" in html
    assert 'id="agentAvatar"' in html
    assert 'id="agentPoster"' in html
    assert 'id="replyCue"' in html
    assert "אווטאר מגיב" in html
    js = client.get("/static/js/meeting.js").text
    assert "respondAsAvatar" in js
    assert "setAgentSpeaking(true)" in js
    css = client.get("/static/css/room.css").text
    assert "me-portrait" in css
    assert "reply-cue" in css
    assert ".visual-tile.speaking #agentAvatar" in css
