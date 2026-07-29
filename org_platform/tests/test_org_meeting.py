"""Legacy meeting API smoke tests updated for SRS roster."""
from __future__ import annotations

import os
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


def test_health_and_meeting_flow(client):
    h = client.get("/api/health").json()
    assert h["ok"] is True
    assert h["agents"] == 21
    created = client.post(
        "/api/meetings",
        json={"title": "Sync", "chair_id": "vp-rd", "seed_intro": True, "morning": True},
    ).json()
    mid = created["meeting"]["id"]
    chat = client.post(
        f"/api/meetings/{mid}/messages",
        json={"text": "Approve release and escalate production incident to CEO"},
    ).json()
    assert len(chat["replies"]) >= 2
    names = {r["sender_name"] for r in chat["replies"]}
    assert "VP R&D (Codex)" in names or any("VP" in n for n in names)
    esc = client.post(
        f"/api/meetings/{mid}/escalate",
        json={"reason": "production financial risk"},
    ).json()
    assert any(r["sender_id"] == "ceo-chanan" for r in esc["replies"]) or any(
        "Chanan" in r["sender_name"] for r in esc["replies"]
    )


def test_one_on_one_meeting_launch(client):
    created = client.post(
        "/api/meetings",
        json={
            "title": "Ultra Agent Meeting 1:1",
            "chair_id": "vp-rd",
            "one_on_one": True,
            "seed_intro": True,
            "morning": False,
        },
    ).json()
    meeting = created["meeting"]
    assert meeting["title"] == "Ultra Agent Meeting 1:1"
    assert meeting["status"] == "live"
    assert set(meeting["participant_ids"]) == {"ceo-chanan", "vp-rd", "dev-tl-cursor"}
    assert any(e.get("type") == "one_on_one" for e in meeting.get("events", []))
    home = client.get("/").text
    assert "oneOnOneLaunch" in home
    assert "Launch 1:1" in home


def test_meeting_simulation_page_and_ensure(client):
    page = client.get("/meeting-simulation.html")
    assert page.status_code == 200
    assert "AI Agent Meeting Simulation" in page.text
    assert "Ultra Agent" in page.text
    ensured = client.post("/api/meetings/one-on-one/ensure").json()
    assert ensured["meeting"]["status"] == "live"
    assert "1:1" in ensured["meeting"]["title"]
    again = client.post("/api/meetings/one-on-one/ensure").json()
    assert again["meeting"]["id"] == ensured["meeting"]["id"]
    assert again["created"] is False
