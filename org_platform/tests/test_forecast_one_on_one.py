"""Forecast 1:1 — hear (mic STT) + see (camera frames)."""
from __future__ import annotations

import base64
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


def _tiny_png_data_url() -> str:
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    return "data:image/png;base64," + base64.b64encode(png).decode()


def test_roster_includes_forecast_agent(client):
    h = client.get("/api/health").json()
    assert h["agents"] == 22
    org = client.get("/api/org").json()
    ids = {a["id"] for a in org["roster"]}
    assert "forecast-maya" in ids


def test_forecast_ensure_and_hear_see(client):
    boot = client.get("/meeting-forecast.html")
    assert boot.status_code == 200
    assert "תחזית" in boot.text

    first = client.post("/api/meetings/forecast/ensure").json()
    assert first["created"] is True
    meeting = first["meeting"]
    mid = meeting["id"]
    assert meeting["status"] == "live"
    assert meeting["chair_id"] == "forecast-maya"
    assert set(meeting["participant_ids"]) == {"ceo-chanan", "forecast-maya"}
    assert any(e.get("type") == "forecast_one_on_one" for e in meeting.get("events", []))
    agent_msgs = [m for m in meeting.get("messages", []) if m.get("kind") == "agent"]
    assert agent_msgs
    # Opening is conversational (meeting style), not a status dump
    assert "פגישת תחזית" in agent_msgs[0]["text"] or "שלום" in agent_msgs[0]["text"]

    second = client.post("/api/meetings/forecast/ensure").json()
    assert second["created"] is False
    assert second["meeting"]["id"] == mid

    # Hear via mic source — continuous meeting turn
    chat = client.post(
        f"/api/meetings/{mid}/messages",
        json={
            "text": "תן לי תחזית על AAPL",
            "sender_id": "ceo-chanan",
            "sender_name": "Me (Chanan Zevin)",
            "heard": True,
            "source": "mic",
        },
    ).json()
    assert len(chat["replies"]) == 1
    reply = chat["replies"][0]
    assert reply["sender_id"] == "forecast-maya"
    assert "AAPL" in reply["text"] or "אופק" in reply["text"]
    assert "Maya Forecast on" not in reply["text"]  # no robotic dump
    assert chat["meeting"]["sense"]["heard"] is True

    # Follow-up turn uses conversation context
    follow = client.post(
        f"/api/meetings/{mid}/messages",
        json={
            "text": "כן, סווינג",
            "sender_id": "ceo-chanan",
            "sender_name": "Me (Chanan Zevin)",
            "heard": True,
            "source": "mic",
        },
    ).json()
    assert follow["replies"][0]["sender_id"] == "forecast-maya"
    assert follow["replies"][0]["meta"]["sense"].get("conversational") is True

    # See via camera frame
    frame = client.post(
        f"/api/meetings/{mid}/frames",
        json={"data_url": _tiny_png_data_url(), "source": "camera", "note": "see-test"},
    ).json()
    assert frame["frame"]["bytes"] > 0
    assert frame["meeting"]["sense"]["seen"] is True
    assert frame["meeting"]["sense"]["frame_count"] >= 1
    assert client.get(frame["frame"]["path"]).status_code == 200
    assert frame.get("ack") is not None
    assert any("רואה" in r["text"] for r in frame["ack"]["replies"])

    dash = client.get("/api/dashboards/executive").json()
    assert dash["forecast_one_on_one"]["live_meeting_id"] == mid
    assert dash["forecast_one_on_one"]["status"] == "live"
