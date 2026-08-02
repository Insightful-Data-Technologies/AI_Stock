"""Tests for AI Capital App Launch Center hub."""
from __future__ import annotations

import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def hub_client(monkeypatch, tmp_path):
    monkeypatch.setenv("HUB_PORT", "4720")
    monkeypatch.setenv("MEETING_PORTS", "3000,4050,4051")
    monkeypatch.setenv("MEETING_PID_FILE", str(tmp_path / "meeting.pid"))
    monkeypatch.setenv("MEETING_PORT_FILE", str(tmp_path / "meeting.port"))
    monkeypatch.setenv("MEETING_LOG_FILE", str(tmp_path / "meeting.log"))
    import importlib
    from app_launch_center import hub as hub_mod

    importlib.reload(hub_mod)
    hub_mod._meeting_proc = None
    hub_mod._active_port = None
    return TestClient(hub_mod.app), hub_mod


def test_hub_home_and_status(hub_client):
    client, _ = hub_client
    home = client.get("/")
    assert home.status_code == 200
    assert "App Launch Center" in home.text
    assert "One on One Meeting" in home.text
    assert "Meeting 41 B" in home.text
    assert "General dashboard" in home.text
    assert "Off" in home.text or "Launch" in home.text

    info = client.get("/api/hub").json()
    assert info["ok"] is True
    assert info["port"] == 4720
    assert info["meeting_port"] == 3000
    assert info["preferred_ports"] == [3000, 4050, 4051]
    assert info["fallback_port"] == 4050

    status = client.get("/api/apps/status").json()
    ids = {a["id"] for a in status["apps"]}
    assert "one-on-one" in ids
    assert "war-room" in ids
    assert "general-dashboard" in ids
    dash = next(a for a in status["apps"] if a["id"] == "general-dashboard")
    assert dash["path"] == "/dashboard"


def test_pick_bind_port_falls_back_when_3000_busy(hub_client):
    client, hub_mod = hub_client

    class BusyHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"not-meeting")

        def log_message(self, *_args):
            return

    # Bind a dummy non-meeting listener on 3000 (or skip if we cannot).
    try:
        server = HTTPServer(("127.0.0.1", 3000), BusyHandler)
    except OSError:
        pytest.skip("port 3000 unavailable for bind in this environment")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert hub_mod._port_open(3000) is True
        assert hub_mod._meeting_healthy_on(3000) is False
        chosen = hub_mod._pick_bind_port()
        assert chosen == 4050
        status = client.get("/api/apps/status").json()
        assert status["next_bind_port"] == 4050
        one = next(a for a in status["apps"] if a["id"] == "one-on-one")
        assert one["port"] == 4050
        assert one["on"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_pick_bind_port_uses_3000_when_free(hub_client):
    _, hub_mod = hub_client
    if hub_mod._port_open(3000):
        pytest.skip("port 3000 already open")
    assert hub_mod._pick_bind_port() == 3000
