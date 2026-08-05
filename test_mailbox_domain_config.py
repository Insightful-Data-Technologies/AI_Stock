#!/usr/bin/env python3
"""Tests for mailbox / domain configuration data and helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

CONFIG_PATH = ROOT / "config" / "mailbox_domain_config.json"


def test_config_schema() -> None:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert data["mailbox"]["imap_host_default"] == "outlook.office365.com"
    assert data["mailbox"]["imap_port_default"] == 993
    assert data["mailbox"]["email_env"] == "MAILBOX_EMAIL"
    assert data["domain_env"] == "GODADDY_DOMAIN"
    assert "spf.protection.outlook.com" in data["dns"]["spf"]["value"]
    assert "mail.protection.outlook.com" in data["dns"]["mx"][0]["points_to_suffix"]
    assert data["dns"]["dmarc"]["name"] == "_dmarc"
    assert len(data["system_overview"]["configured_features_templates"]) >= 5


def test_apply_mailbox_dns_helpers() -> None:
    import apply_mailbox_dns as dns

    sample = "example.com"
    assert dns.expected_mx(sample) == "example-com.mail.protection.outlook.com"
    assert dns.SPF_VALUE.startswith("v=spf1")
    assert "spf.protection.outlook.com" in dns.SPF_VALUE
    assert "ASPMX.L.GOOGLE" not in dns.SPF_VALUE


def test_resolve_runtime_from_env(monkeypatch_env: bool = True) -> None:
    # Keep secrets out of source; use generic fixture values.
    os.environ["MAILBOX_EMAIL"] = "user@example.com"
    os.environ["GODADDY_DOMAIN"] = "example.com"
    os.environ["MAILBOX_IMAP_HOST"] = "outlook.office365.com"
    os.environ["MAILBOX_IMAP_PORT"] = "993"
    os.environ["MAILBOX_APP_PASSWORD"] = ""

    # Import after env is set
    import importlib

    if "mailbox_domain_config_app" in sys.modules:
        del sys.modules["mailbox_domain_config_app"]

    # Avoid launching Streamlit page config side effects by compiling only.
    src = (ROOT / "tools" / "mailbox_domain_config_app.py").read_text(encoding="utf-8")
    compile(src, "mailbox_domain_config_app.py", "exec")
    assert "MAILBOX_APP_PASSWORD" in src
    assert "Mailbox & Domain Configuration" in src

    from apply_mailbox_dns import expected_mx

    assert expected_mx(os.environ["GODADDY_DOMAIN"]).endswith(
        ".mail.protection.outlook.com"
    )


if __name__ == "__main__":
    test_config_schema()
    test_apply_mailbox_dns_helpers()
    test_resolve_runtime_from_env()
    print("All mailbox domain config tests passed.")
