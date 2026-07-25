"""VP Delivery Studio tests — screen frame + DevOps handoff."""
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


def _tiny_png_data_url():
    # 1x1 PNG
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    return "data:image/png;base64," + base64.b64encode(png).decode()


def test_studio_screen_and_devops_delivery(client):
    assert client.get("/studio").status_code == 200
    created = client.post("/api/studio/sessions", json={"title": "Studio Test"}).json()
    sid = created["session"]["id"]
    assert created["session"]["messages"]

    share = client.post(f"/api/studio/sessions/{sid}/share", json={"active": True}).json()
    assert share["active"] is True

    frame = client.post(
        f"/api/studio/sessions/{sid}/frames",
        json={"data_url": _tiny_png_data_url(), "note": "unit"},
    ).json()["frame"]
    assert frame["bytes"] > 0
    assert client.get(frame["path"]).status_code == 200

    chat = client.post(
        f"/api/studio/sessions/{sid}/messages",
        json={
            "text": "Please deploy the new health dashboard to Cloud Run and verify HTTPS",
            "sender_id": "ceo-chanan",
            "sender_name": "Me (Chanan Zevin)",
        },
    ).json()
    assert chat["vp"]["sender_id"] == "vp-rd"
    assert "screen" in chat["vp"]["text"].lower() or "frame" in chat["vp"]["text"].lower()

    delivered = client.post(
        f"/api/studio/sessions/{sid}/deliver",
        json={
            "briefing": "Deploy the new health dashboard to Cloud Run and verify HTTPS",
            "owner": "devops-1",
            "priority": "P1",
        },
    ).json()
    assert delivered["task"]["owner"] == "devops-1"
    assert delivered["task"]["status"] == "assigned"
    assert delivered["delivery"]["task_id"] == delivered["task"]["id"]
    assert any(e.get("type") == "screen_share_frame" for e in delivered["task"]["evidence"])

    # slack channel got the delivery
    msgs = client.get("/api/channels/devops/messages").json()["messages"]
    assert any(delivered["task"]["id"] in m["text"] for m in msgs)
