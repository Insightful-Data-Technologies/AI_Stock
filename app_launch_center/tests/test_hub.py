"""Tests for AI Capital App Launch Center hub."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def hub_client(monkeypatch):
    monkeypatch.setenv("HUB_PORT", "4720")
    monkeypatch.setenv("MEETING_PORT", "3000")
    from app_launch_center import hub as hub_mod

    return TestClient(hub_mod.app)


def test_hub_home_and_status(hub_client):
    home = hub_client.get("/")
    assert home.status_code == 200
    assert "App Launch Center" in home.text
    assert "One on One Meeting" in home.text
    assert "Off" in home.text or "Launch" in home.text

    info = hub_client.get("/api/hub").json()
    assert info["ok"] is True
    assert info["port"] == 4720
    assert info["meeting_port"] == 3000

    status = hub_client.get("/api/apps/status").json()
    ids = {a["id"] for a in status["apps"]}
    assert "one-on-one" in ids
    assert "war-room" in ids
