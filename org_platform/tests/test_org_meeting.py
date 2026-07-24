"""Unit + API tests for enterprise org meeting platform."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["ORG_DATA_DIR"] = "/tmp/org_platform_test_data"

from org_platform.agents.engine import generate_live_responses, route_speakers
from org_platform.agents.roster import CEO_ID, ROSTER, SUPER_ADMIN_ID, public_roster
from org_platform.api.app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path))
    from org_platform.store import meetings as meetings_mod
    from org_platform.api import app as app_mod

    meetings_mod.STORE = meetings_mod.MeetingStore(str(tmp_path))
    # ensure app module sees fresh store via _store()
    return TestClient(app_mod.app)


def test_roster_has_required_roles():
    roles = {a.role.value for a in ROSTER.values()}
    assert "ceo" in roles
    assert "vp_rd" in roles
    assert "project_manager" in roles
    assert "developer" in roles
    assert "qa_lead" in roles
    assert "devops_lead" in roles
    assert "it_lead" in roles
    assert SUPER_ADMIN_ID in ROSTER
    assert ROSTER[CEO_ID].name == "Chanan Zevin"
    assert ROSTER[SUPER_ADMIN_ID].can_approve is True
    assert len(public_roster()) >= 12


def test_super_admin_approves():
    replies, events = generate_live_responses(
        "Please approve the production deploy",
        meeting_title="Release Gate",
    )
    assert any(r["agent_id"] == SUPER_ADMIN_ID for r in replies)
    assert any(e["type"] == "approval" for e in events)
    assert any(r.get("approval") for r in replies)


def test_escalation_reaches_ceo():
    speakers = route_speakers("critical outage escalate to CEO now")
    assert SUPER_ADMIN_ID in speakers
    assert CEO_ID in speakers
    replies, events = generate_live_responses(
        "critical sev-1 outage — escalate",
        meeting_title="Incident",
    )
    assert any(r["agent_id"] == CEO_ID for r in replies)
    assert any(e["type"] == "escalation" for e in events) or any(
        r["agent_id"] == CEO_ID for r in replies
    )


def test_health_and_org(client):
    h = client.get("/api/health")
    assert h.status_code == 200
    assert h.json()["ok"] is True
    assert h.json()["agents"] >= 12
    org = client.get("/api/org")
    assert org.status_code == 200
    assert org.json()["ceo"] == "Chanan Zevin"


def test_meeting_flow_e2e(client):
    created = client.post(
        "/api/meetings",
        json={"title": "E2E Delivery Sync", "chair_id": SUPER_ADMIN_ID, "seed_intro": True},
    )
    assert created.status_code == 200
    meeting = created.json()["meeting"]
    mid = meeting["id"]
    assert meeting["status"] == "live"
    assert len(meeting["messages"]) >= 2

    chat = client.post(
        f"/api/meetings/{mid}/messages",
        json={"text": "Approve release and confirm QA + DevOps readiness"},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["human"]["text"].startswith("Approve")
    assert len(body["replies"]) >= 2
    assert any(r["sender_id"] == SUPER_ADMIN_ID for r in body["replies"])

    esc = client.post(
        f"/api/meetings/{mid}/escalate",
        json={"reason": "Need CEO visibility on launch risk"},
    )
    assert esc.status_code == 200
    assert any(r["sender_id"] == CEO_ID for r in esc.json()["replies"])

    got = client.get(f"/api/meetings/{mid}")
    assert got.status_code == 200
    assert got.json()["meeting"]["messages"]
    assert got.json()["meeting"]["events"]

    ended = client.post(f"/api/meetings/{mid}/end")
    assert ended.status_code == 200
    assert ended.json()["meeting"]["status"] == "ended"

    history = client.get("/api/meetings")
    assert any(m["id"] == mid for m in history.json()["meetings"])


def test_pages(client):
    assert client.get("/").status_code == 200
    assert "Insightful Data Technologies" in client.get("/").text
    created = client.post("/api/meetings", json={"title": "UI Room", "seed_intro": False})
    mid = created.json()["meeting"]["id"]
    page = client.get(f"/meeting/{mid}")
    assert page.status_code == 200
    assert "Visible participants" in page.text
