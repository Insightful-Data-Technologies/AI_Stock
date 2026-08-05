"""AI Capital — Mailbox & Domain Configuration (Microsoft 365)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MAILBOX_EMAIL", "user@example.com")
    monkeypatch.setenv("GODADDY_DOMAIN", "example.com")
    monkeypatch.setenv("MAILBOX_IMAP_HOST", "outlook.office365.com")
    monkeypatch.setenv("MAILBOX_IMAP_PORT", "993")
    monkeypatch.delenv("MAILBOX_APP_PASSWORD", raising=False)
    from org_platform.store import platform as platform_mod
    from org_platform.api import app as app_mod

    platform_mod.rebind(str(tmp_path))
    return TestClient(app_mod.app)


def test_mailbox_page_and_prefilled_api(client):
    page = client.get("/mailbox-domain-config")
    assert page.status_code == 200
    assert b"Mailbox & Domain Configuration" in page.content

    cfg = client.get("/api/mailbox-domain-config").json()
    assert cfg["mailbox"]["email"] == "user@example.com"
    assert cfg["mailbox"]["imap_host"] == "outlook.office365.com"
    assert cfg["mailbox"]["imap_port"] == 993
    assert cfg["mailbox"]["app_password_set"] is False
    assert cfg["domain"] == "example.com"
    assert "outlook.com" in cfg["dns"]["mx"][0]["points_to"]
    assert "spf.protection.outlook.com" in cfg["dns"]["spf"]["value"]
    assert "Google MX" in cfg["dns"]["provider_note"] or "not Google" in cfg["dns"]["provider_note"]
    assert any("user@example.com" in f for f in cfg["system_overview"]["configured_features"])


def test_mailbox_save_omits_password_from_disk(client, tmp_path):
    res = client.post(
        "/api/mailbox-domain-config",
        json={
            "email": "ops@example.com",
            "imap_host": "outlook.office365.com",
            "imap_port": 993,
            "app_password": "secret-app-password-value",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["app_password_set"] is True
    saved_path = tmp_path / "mailbox_domain_config.json"
    disk = saved_path.read_text(encoding="utf-8")
    assert "secret-app-password-value" not in disk
    assert "ops@example.com" in disk
