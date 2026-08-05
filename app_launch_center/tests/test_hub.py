"""Tests for Launch Center buttons — yellow On, no Off·3000."""
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


def test_home_has_yellow_and_meeting_buttons(hub_client):
    client, _ = hub_client
    home = client.get("/")
    assert home.status_code == 200
    assert "General dashboard" in home.text
    assert "Meeting Room" in home.text
    assert "One on One Meeting" in home.text
    assert "Multi-Agent War Room" in home.text
    assert "Content Studio" in home.text
    assert "Launch" in home.text
    assert "Open Link" in home.text
    assert "Off · 3000" not in home.text


def test_all_apps_on_current_port_not_3000(hub_client):
    client, _ = hub_client
    status = client.get("/api/apps/status", headers={"host": "127.0.0.1:4720"}).json()
    assert status["active_port"] == 4720
    ids = {a["id"] for a in status["apps"]}
    assert "general-dashboard" in ids
    assert "meeting-room" in ids
    assert "one-on-one" in ids
    assert "war-room" in ids
    assert "content-studio" in ids
    for app in status["apps"]:
        assert app["on"] is True
        assert app["port"] == 4720
        assert app["port"] != 3000


def test_launch_buttons_go_to_paths(hub_client):
    client, _ = hub_client
    for app_id, path in [
        ("general_dashboard", "/dashboard"),
        ("meeting_room", "/meeting-room"),
        ("one_on_one", "/meeting-room"),
        ("war_room", "/meeting-room"),
        ("content_studio", "/content-studio"),
    ]:
        res = client.post(
            "/api/apps/launch",
            json={"id": app_id},
            headers={"host": "127.0.0.1:4720"},
        ).json()
        assert res["ok"] is True
        assert res["path"] == path
        assert res["port"] == 4720


def test_meeting_room_page(hub_client):
    client, _ = hub_client
    page = client.get("/meeting-room")
    assert page.status_code == 200
    assert "cabinet-room.png" in page.text


def test_content_studio_page_via_hub(hub_client):
    client, _ = hub_client
    page = client.get("/content-studio")
    assert page.status_code == 200
    assert "Rewrite" in page.text
    run = client.post(
        "/api/content-studio/run",
        json={"mode": "rewrite", "text": "Rates held steady.", "tone": "executive"},
    )
    assert run.status_code == 200
    assert run.json()["ok"] is True
    assert "DeploymentNotFound" not in run.json()["text"]
