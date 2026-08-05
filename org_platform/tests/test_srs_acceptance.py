"""SRS §19 acceptance tests for AI Capital Enterprise Team."""
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


def test_company_branding(client):
    c = client.get("/api/company").json()
    assert "2.o AI" in c["legal_name"]
    assert c["ceo"] == "Chanan Zevin"
    assert "Risk Management" in c["tagline"]
    home = client.get("/")
    assert home.status_code == 200
    assert "Insightful Data Technologies – 2.o AI" in home.text
    assert "Chanan Zevin – CEO" in home.text


def test_hierarchy_complete(client):
    org = client.get("/api/org").json()
    ids = {a["id"] for a in org["roster"]}
    required = {
        "ceo-chanan",
        "ea-sofia",
        "vp-rd",
        "pm-main",
        "pm-dev-claude",
        "pm-devops",
        "dev-tl-cursor",
        "dev-ultra-1",
        "dev-ultra-2",
        "dev-ultra-3",
        "qa-tl",
        "qa-1",
        "qa-2",
        "qa-3",
        "devops-tl",
        "devops-1",
        "devops-2",
        "devops-3",
        "it-tl",
        "it-1",
        "it-2",
    }
    assert required.issubset(ids)
    assert len(org["roster"]) == 22


def test_channels_and_email_simulated(client):
    ch = client.get("/api/channels").json()["channels"]
    names = {c["id"] for c in ch}
    for required in [
        "executive-management",
        "company-announcements",
        "project-management",
        "development",
        "qa",
        "devops",
        "it-support",
        "production-incidents",
        "release-approvals",
        "agent-reports",
    ]:
        assert required in names
    email = client.post(
        "/api/email/send",
        json={
            "from_id": "it-1",
            "to_email": "vp.rd@insightfuldata.ai",
            "subject": "test",
            "body": "hello",
        },
    ).json()
    assert email["email"]["mode"] == "SIMULATED"
    assert "not be presented as real" in email["warning"].lower() or "SIMULATED" in email["warning"] or "simulated" in email["warning"].lower()


def test_all_agents_pass_comm_tests(client):
    result = client.post("/api/comm-tests/run-all").json()
    assert result["status"] == "PASS"
    assert result["passed"] == result["tested"]
    assert result["email_mode"]["mode"] == "SIMULATED"


def test_srs_e2e_workflow(client):
    result = client.post("/api/workflows/e2e-demo").json()
    assert result["status"] == "PASS"
    assert result["dev_task"]["status"] == "completed"
    assert result["dev_task"]["qa_decision"]["decision"] == "PASS"
    assert result["dev_task"]["evidence"]
    assert result["deploy_task"]["status"] == "completed"
    assert result["morning_meeting_id"]
    assert result["executive_summary"]["prepared_by"] == "ea-sofia"
    assert result["audit_events"] > 10
    # dashboards
    assert client.get("/api/dashboards/executive").status_code == 200
    assert client.get("/api/dashboards/management").status_code == 200
    assert client.get("/api/dashboards/communication").status_code == 200
    # meeting page
    mid = result["morning_meeting_id"]
    page = client.get(f"/meeting/{mid}")
    assert page.status_code == 200
    assert "2.o AI" in page.text


def test_task_definition_of_done_gate(client):
    task = client.post(
        "/api/tasks",
        json={
            "title": "Needs evidence",
            "description": "x",
            "created_by": "pm-dev-claude",
            "acceptance_criteria": ["evidence"],
        },
    ).json()["task"]
    # cannot approve without QA PASS + evidence
    bad = client.post(f"/api/tasks/{task['id']}/approve", json={"by": "vp-rd", "note": "nope"})
    assert bad.status_code == 400
