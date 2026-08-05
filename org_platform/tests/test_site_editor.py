"""Site Editor CMS tests — no SQL crash, buttons wired."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path / "org_data"))
    monkeypatch.delenv("DB_CONN_STR", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    import importlib
    from org_platform.api import app as app_mod

    importlib.reload(app_mod)
    return TestClient(app_mod.app)


def test_site_editor_page(client):
    page = client.get("/site-editor")
    assert page.status_code == 200
    assert "Site Editor CMS" in page.text
    assert "Operations" in page.text
    assert "Create MD Document" in page.text
    assert "Create ticket" in page.text
    assert "Project Details" in page.text


def test_db_status_never_crashes(client):
    res = client.get("/api/site-editor/db-status")
    assert res.status_code == 200
    data = res.json()
    assert "ok" in data
    assert data.get("mode") in {"local", "sqlserver"}
    blob = str(data)
    assert "sqlalchemy.exc.InterfaceError" not in blob


def test_create_ticket_and_md(client):
    tk = client.post(
        "/api/site-editor/tickets",
        json={"title": "Ops check", "body": "from test", "priority": "P1"},
    ).json()
    assert tk["ok"] is True
    assert tk["ticket"]["id"].startswith("T-")

    md = client.post(
        "/api/site-editor/documents",
        json={"title": "Note", "content": "# Note\n"},
    ).json()
    assert md["ok"] is True
    assert md["document"]["id"].startswith("MD-")

    tickets = client.get("/api/site-editor/tickets").json()["tickets"]
    docs = client.get("/api/site-editor/documents").json()["documents"]
    assert any(t["title"] == "Ops check" for t in tickets)
    assert any(d["title"] == "Note" for d in docs)


def test_project_details(client):
    data = client.get("/api/site-editor/project").json()
    assert data["ok"] is True
    assert "Site Editor CMS" in data["project"]["product"]
