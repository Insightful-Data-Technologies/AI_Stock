"""AI Capital — target mailbox & domain configuration (Microsoft 365 IMAP)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from org_platform.publish.env_loader import load_dotenv

load_dotenv()

CONFIG_SCHEMA = Path(__file__).resolve().parent / "domain_config_schema.json"


def _domain() -> str:
    return (os.getenv("GODADDY_DOMAIN") or os.getenv("MAILBOX_DOMAIN") or "").strip()


def _email() -> str:
    return (os.getenv("MAILBOX_EMAIL") or "").strip()


def _dashed(domain: str) -> str:
    return domain.replace(".", "-") if domain else ""


def resolve_config() -> Dict[str, Any]:
    """Return UI-ready config. Secrets stay in env; password never returned in cleartext."""
    load_dotenv()
    schema = json.loads(CONFIG_SCHEMA.read_text(encoding="utf-8"))
    domain = _domain()
    email = _email()
    dashed = _dashed(domain)
    password = os.getenv("MAILBOX_APP_PASSWORD") or ""
    imap_host = (os.getenv("MAILBOX_IMAP_HOST") or schema["mailbox"]["imap_host_default"]).strip()
    imap_port = int(os.getenv("MAILBOX_IMAP_PORT") or schema["mailbox"]["imap_port_default"])

    mx_target = (
        f"{dashed}.mail.protection.outlook.com"
        if dashed
        else "(set GODADDY_DOMAIN)"
    )
    dmarc = schema["dns"]["dmarc"]["value_template"].replace("{domain}", domain or "{domain}")
    supporting = []
    for row in schema["dns"]["supporting_templates"]:
        item = {"type": row["type"], "name": row["name"]}
        if "value" in row:
            item["value"] = row["value"]
        else:
            item["value"] = row["value_template"].replace("{domain-dashed}", dashed or "{domain}")
        supporting.append(item)

    features = [
        t.replace("{email}", email or "{email}")
        for t in schema["system_overview"]["configured_features_templates"]
    ]

    return {
        "title": schema["title"],
        "subtitle": schema["subtitle"],
        "organization": schema["organization"],
        "domain": domain,
        "domain_set": bool(domain),
        "mailbox": {
            "email": email,
            "email_set": bool(email),
            "imap_host": imap_host,
            "imap_port": imap_port,
            "app_password_set": bool(password.strip()),
            "auth_note": schema["mailbox"]["auth_note"],
        },
        "dns": {
            "provider_note": schema["dns"]["provider_note"],
            "mx": [{"priority": 0, "host": "@", "points_to": mx_target}],
            "spf": schema["dns"]["spf"],
            "dmarc": {"name": "_dmarc", "value": dmarc},
            "supporting": supporting,
        },
        "system_overview": {
            "heading": schema["system_overview"]["heading"],
            "configured_features": features,
        },
        "mode": "MICROSOFT_365" if password.strip() else "PENDING_APP_PASSWORD",
    }


def save_non_secret_fields(payload: Dict[str, Any], data_dir: Path) -> Dict[str, Any]:
    """Persist non-secret mailbox settings under ORG_DATA_DIR (never write app password)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "email": (payload.get("email") or "").strip(),
        "imap_host": (payload.get("imap_host") or "outlook.office365.com").strip(),
        "imap_port": int(payload.get("imap_port") or 993),
        "app_password_set": bool((payload.get("app_password") or "").strip())
        or bool((os.getenv("MAILBOX_APP_PASSWORD") or "").strip()),
        # Intentionally omit app_password from disk.
    }
    path = data_dir / "mailbox_domain_config.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out
