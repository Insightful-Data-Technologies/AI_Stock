"""Tests for button-only Launch Center on 4720 / 4600."""
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


def test_home_is_buttons(hub_client):
    client, _ = hub_client
    home = client.get("/")
    assert home.status_code == 200
    assert "Open Meeting Room" in home.text
    assert "Open Dashboard" in home.text
    assert "4720" in home.text
    assert "4600" in home.text

    apps = client.get("/apps")
    assert apps.status_code == 200
    assert "Open Meeting Room" in apps.text


def test_hub_status_uses_request_port(hub_client):
    client, _ = hub_client
    info = client.get("/api/hub", headers={"host": "127.0.0.1:4600"}).json()
    assert info["ok"] is True
    assert info["port"] == 4600
    assert info["mode"] == "buttons_only"
    assert 4720 in info["preferred_ports"]
    assert 4600 in info["preferred_ports"]

    status = client.get("/api/apps/status", headers={"host": "127.0.0.1:4720"}).json()
    assert status["active_port"] == 4720
    ids = {a["id"] for a in status["apps"]}
    assert ids == {"meeting-room", "general-dashboard"}
    for app in status["apps"]:
        assert app["port"] == 4720
        assert app["on"] is True


def test_launch_buttons(hub_client):
    client, _ = hub_client
    meeting = client.post(
        "/api/apps/launch",
        json={"id": "meeting_room"},
        headers={"host": "127.0.0.1:4720"},
    ).json()
    assert meeting["ok"] is True
    assert meeting["path"] == "/meeting-room"
    assert meeting["port"] == 4720
    assert meeting["url"].endswith("/meeting-room")

    dash = client.post(
        "/api/apps/launch",
        json={"id": "dashboard"},
        headers={"host": "127.0.0.1:4600"},
    ).json()
    assert dash["path"] == "/dashboard"
    assert dash["port"] == 4600


def test_meeting_room_still_on_same_app(hub_client):
    client, _ = hub_client
    page = client.get("/meeting-room")
    assert page.status_code == 200
    assert "cabinet-room.png" in page.text
    assert "_XwN09djHuM" in page.text


def test_stop_noop(hub_client):
    client, _ = hub_client
    stopped = client.post("/api/apps/stop").json()
    assert stopped["ok"] is True
