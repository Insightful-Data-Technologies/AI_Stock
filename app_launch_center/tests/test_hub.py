"""Tests for AI Capital App Launch Center hub (embedded on :4720)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))


@pytest.fixture()
def hub_client(monkeypatch, tmp_path):
    monkeypatch.setenv("HUB_PORT", "4720")
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path / "org_data"))
    import importlib
    from app_launch_center import hub as hub_mod

    importlib.reload(hub_mod)
    return TestClient(hub_mod.app), hub_mod


def test_hub_home_and_status(hub_client):
    client, hub_mod = hub_client
    apps = client.get("/apps")
    assert apps.status_code == 200
    assert "App Launch Center" in apps.text
    assert "Meeting Room" in apps.text
    assert "General dashboard" in apps.text

    info = client.get("/api/hub").json()
    assert info["ok"] is True
    assert info["port"] == 4720
    assert info["meeting_port"] == 4720
    assert info["preferred_ports"] == [4720]
    assert info["mode"] == "single_port_embedded"
    assert info["apps_path"] == "/apps"

    status = client.get("/api/apps/status").json()
    ids = {a["id"] for a in status["apps"]}
    assert "meeting-room" in ids
    assert "meeting-41b" in ids
    assert "general-dashboard" in ids
    assert status["active_port"] == 4720
    assert status["embedded"] is True
    for app in status["apps"]:
        assert app["port"] == 4720
        assert app["on"] is True
        assert "4720" in app["url"]


def test_launch_apps_stay_on_4720(hub_client):
    client, _ = hub_client
    for app_id, path in [
        ("meeting_room", "/meeting-room"),
        ("meeting_41b", "/meeting-room"),
        ("one_on_one", "/meeting-room"),
        ("war_room", "/meeting-room"),
        ("general_dashboard", "/dashboard"),
    ]:
        res = client.post("/api/apps/launch", json={"id": app_id}).json()
        assert res["ok"] is True
        assert res["port"] == 4720
        assert res["status"] == "On"
        assert res["url"].endswith(path)
        assert "4720" in res["url"]


def test_meeting_room_cinema_on_same_app(hub_client):
    client, _ = hub_client
    health = client.get("/api/health").json()
    assert health["ok"] is True
    assert health["service"] == "ai-capital-enterprise-team"

    page = client.get("/meeting-room")
    assert page.status_code == 200
    assert "cabinet-room.png" in page.text
    assert "_XwN09djHuM" in page.text

    legacy = client.get("/meeting-41b.html")
    assert legacy.status_code == 200
    assert "meeting-room" in legacy.text.lower()


def test_stop_is_noop_when_embedded(hub_client):
    client, _ = hub_client
    stopped = client.post("/api/apps/stop").json()
    assert stopped["ok"] is True
    assert stopped["stopped"] is False
