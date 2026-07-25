"""Domain publisher — Google Studio URL → GoDaddy DNS plan/publish."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("GODADDY_API_KEY", raising=False)
    monkeypatch.delenv("GODADDY_API_SECRET", raising=False)
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path))
    from org_platform.store import platform as platform_mod
    from org_platform.api import app as app_mod

    platform_mod.rebind(str(tmp_path))
    return TestClient(app_mod.app)


def test_publish_page_and_dry_run(client):
    assert client.get("/publish").status_code == 200
    plan = client.post(
        "/api/publish/plan",
        json={
            "site_url": "https://my-cool-app.web.app",
            "domain": "aizevinstocks.com",
        },
    ).json()["plan"]
    assert plan["studio"]["kind"] == "firebase_hosting"
    assert plan["studio"]["host"] == "my-cool-app.web.app"
    assert any(r["type"] == "CNAME" and r["name"] == "www" for r in plan["records"])
    assert plan["public_urls"]["www"] == "https://www.aizevinstocks.com"

    published = client.post(
        "/api/publish",
        json={
            "site_url": "https://my-cool-app.web.app",
            "domain": "aizevinstocks.com",
            "dry_run": True,
        },
    ).json()
    assert published["status"] == "planned"
    assert published["application"]["mode"] == "dry_run"
    assert published["job"]["domain"] == "aizevinstocks.com"
    assert "api_key" not in published["job"]
    jobs = client.get("/api/publish/jobs").json()["jobs"]
    assert len(jobs) == 1


def test_live_publish_mocked_godaddy(client):
    with patch("org_platform.publish.publisher.GoDaddyClient") as MockClient:
        inst = MockClient.return_value
        inst.configured = True
        inst.get_domain.return_value = {"domain": "example.com"}
        inst.put_record.return_value = None
        inst.set_forwarding.return_value = (True, "apex forwarding configured")

        res = client.post(
            "/api/publish",
            json={
                "site_url": "https://demo.run.app",
                "domain": "example.com",
                "dry_run": False,
                "api_key": "key",
                "api_secret": "secret",
            },
        ).json()

    assert res["status"] == "published"
    assert res["application"]["applied"] is True
    assert any(r.get("action") == "put_record" and r.get("ok") for r in res["application"]["results"])
    # devops notified
    msgs = client.get("/api/channels/devops/messages").json()["messages"]
    assert any("Domain publish" in m["text"] for m in msgs)


def test_invalid_domain(client):
    bad = client.post("/api/publish/plan", json={"site_url": "https://x.web.app", "domain": "not a domain"})
    assert bad.status_code == 400
