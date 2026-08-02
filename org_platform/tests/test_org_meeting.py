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
    assert page.headers.get("content-type", "").startswith("text/html")

    first = client.post("/api/meetings/one-on-one/ensure").json()
    assert first["created"] is True
    mid = first["meeting"]["id"]
    assert first["meeting"]["status"] == "live"

    second = client.post("/api/meetings/one-on-one/ensure").json()
    assert second["created"] is False
    assert second["meeting"]["id"] == mid


def test_dashboard_one_on_one_box(client):
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    assert "dashboardOneOnOne" in dash.text
    assert "General dashboard · One on One" in dash.text
    assert "dashLaunchOneOnOne" in dash.text
    assert "Ultra Agent Meeting 1:1" in dash.text

    created = client.post("/api/meetings/one-on-one/ensure").json()
    exec_dash = client.get("/api/dashboards/executive").json()
    assert exec_dash["one_on_one"]["available"] is True
    assert exec_dash["one_on_one"]["live_meeting_id"] == created["meeting"]["id"]
    assert exec_dash["one_on_one"]["status"] == "live"


def test_meeting_41b_visuals_ensure_and_avatar(client):
    page = client.get("/meeting-41b.html")
    assert page.status_code == 200
    assert "Meeting 41 B" in page.text

    home = client.get("/").text
    assert "meeting41bLaunch" in home
    assert "Launch 41 B" in home

    dash = client.get("/dashboard").text
    assert "dashboard41b" in dash
    assert "dashLaunch41b" in dash

    first = client.post("/api/meetings/41b/ensure").json()
    assert first["created"] is True
    meeting = first["meeting"]
    assert meeting["title"] == "Meeting 41 B · Visuals"
    assert meeting["status"] == "live"
    assert "ceo-chanan" in meeting["participant_ids"]
    assert "ea-sofia" in meeting["participant_ids"]
    assert any(e.get("type") == "meeting_41b" for e in meeting.get("events", []))
    assert first["avatar"]["ready"] is True

    second = client.post("/api/meetings/41b/ensure").json()
    assert second["created"] is False
    assert second["meeting"]["id"] == meeting["id"]

    room = client.get(f"/meeting/{meeting['id']}")
    assert room.status_code == 200
    assert "visualStage" in room.text
    assert "meCamera" in room.text
    assert "agentAvatar" in room.text
    assert "shareBtn" in room.text

    avatar = client.get("/api/meetings/41b/avatar").json()
    assert avatar["video_path"] == "/static/assets/avatar/agent-girl.mp4"
    assert avatar["poster_path"] == "/static/assets/avatar/agent-girl.png"
    assert avatar["video_bytes"] > 10000

    exec_dash = client.get("/api/dashboards/executive").json()
    assert exec_dash["meeting_41b"]["live_meeting_id"] == meeting["id"]
    assert "human-avatar" in exec_dash["meeting_41b"]["features"]


def test_meeting_41b_avatar_upload_isolated(client, tmp_path, monkeypatch):
    from org_platform.api import app as app_mod

    avatar_dir = tmp_path / "avatar"
    avatar_dir.mkdir()
    poster = avatar_dir / "agent-girl.png"
    video = avatar_dir / "agent-girl.mp4"
    poster.write_bytes(b"png")
    video.write_bytes(b"seed-video-bytes-xxxxxxxxxxxx")
    monkeypatch.setattr(app_mod, "AVATAR_DIR", avatar_dir)
    monkeypatch.setattr(app_mod, "AVATAR_VIDEO", video)
    monkeypatch.setattr(app_mod, "AVATAR_POSTER", poster)

    tiny = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2000
    uploaded = client.post(
        "/api/meetings/41b/avatar",
        files={"file": ("2026-08-03_01-01-17.mp4", tiny, "video/mp4")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["ok"] is True
    assert video.read_bytes() == tiny
