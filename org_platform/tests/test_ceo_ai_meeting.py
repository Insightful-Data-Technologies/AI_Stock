"""CEO meeting — cinema presence, no Hold-to-talk / transcript chrome."""
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


def test_ceo_meeting_cinema_no_hold_no_transcript(client):
    page = client.get("/ceo-ai-meeting.html")
    assert page.status_code == 200
    html = page.text
    assert "Hold to talk" not in html
    assert 'id="transcript"' not in html
    assert "ceo-chanan.png" in html
    assert "_XwN09djHuM" in html
    assert "agent-girl.mp4" in html
    assert "drift" in html  # cinema motion
    assert 'id="writeForm"' in html
    assert "classList.toggle" in html or 'writeForm"' in html


def test_gossip_led_replies(client):
    mid = client.post("/api/meetings/forecast/ensure").json()["meeting"]["id"]
    r1 = client.post(
        f"/api/meetings/{mid}/messages",
        json={"text": "היי", "heard": True, "source": "mic", "sender_id": "ceo-chanan"},
    ).json()["replies"][0]["text"]
    assert "תוביל" in r1 or "איתך" in r1
    assert "Maya Forecast on" not in r1
    assert "bias" not in r1.lower()

    r2 = client.post(
        f"/api/meetings/{mid}/messages",
        json={"text": "תגיד לי על AAPL ברכילות", "heard": True, "source": "mic", "sender_id": "ceo-chanan"},
    ).json()["replies"][0]
    assert r2["meta"]["sense"]["style"] == "gossip-led"
    assert len(r2["text"]) < 160
