#!/usr/bin/env python3
"""
Mailbox & Domain Configuration — dark-blue settings UI.

Pre-fills mailbox, Microsoft 365 DNS, and system overview from
config/mailbox_domain_config.json plus environment variables.
App password is read from MAILBOX_APP_PASSWORD (never committed).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "mailbox_domain_config.json"

load_dotenv(ROOT / ".env")


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def domain_dashed(domain: str) -> str:
    return domain.replace(".", "-")


def resolve_runtime(cfg: dict[str, Any]) -> dict[str, Any]:
    """Fill templates from environment (secrets stay out of the repo)."""
    mail_cfg = cfg["mailbox"]
    domain = os.getenv(cfg.get("domain_env", "GODADDY_DOMAIN"), "").strip()
    email = os.getenv(mail_cfg["email_env"], "").strip()
    imap_host = os.getenv(
        mail_cfg["imap_host_env"],
        mail_cfg.get("imap_host_default", "outlook.office365.com"),
    ).strip()
    imap_port = str(
        os.getenv(
            mail_cfg["imap_port_env"],
            str(mail_cfg.get("imap_port_default", 993)),
        )
    ).strip()
    app_password = os.getenv(mail_cfg["app_password_env"], "")

    dashed = domain_dashed(domain) if domain else "{domain}"
    mx_target = (
        f"{dashed}.mail.protection.outlook.com"
        if domain
        else "(set GODADDY_DOMAIN / MAILBOX_EMAIL in .env)"
    )
    dmarc = cfg["dns"]["dmarc"]["value_template"].replace(
        "{domain}", domain or "{domain}"
    )
    supporting = []
    for row in cfg["dns"].get("supporting_templates", []):
        item = {"type": row["type"], "name": row["name"]}
        if "value" in row:
            item["value"] = row["value"]
        else:
            item["value"] = row.get("value_template", "").replace(
                "{domain-dashed}", dashed
            )
        supporting.append(item)

    features = [
        t.replace("{email}", email or "{email}")
        for t in cfg["system_overview"]["configured_features_templates"]
    ]

    return {
        "domain": domain,
        "email": email,
        "imap_host": imap_host,
        "imap_port": imap_port,
        "app_password": app_password,
        "mx_target": mx_target,
        "dmarc": dmarc,
        "supporting": supporting,
        "features": features,
        "organization": cfg.get("organization", ""),
    }


CFG = load_config()
RT = resolve_runtime(CFG)
MAIL = CFG["mailbox"]
DNS = CFG["dns"]
OVERVIEW = CFG["system_overview"]

st.set_page_config(
    page_title="Mailbox & Domain Configuration",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap");

      :root {
        --bg: #0b1220;
        --panel: #111a2b;
        --panel-2: #162033;
        --line: #243247;
        --text: #e8eef7;
        --muted: #8fa3bc;
        --accent: #3b82f6;
        --accent-2: #60a5fa;
        --ok: #34d399;
        --warn: #fbbf24;
      }

      .stApp {
        background:
          radial-gradient(900px 420px at 15% -10%, rgba(59,130,246,0.18), transparent 55%),
          radial-gradient(700px 380px at 90% 0%, rgba(14,165,233,0.12), transparent 50%),
          linear-gradient(180deg, #070d18 0%, var(--bg) 40%, #0a1424 100%);
        color: var(--text);
        font-family: "IBM Plex Sans", sans-serif;
      }

      #MainMenu, footer, header { visibility: hidden; }

      .modal {
        background: linear-gradient(180deg, #121c30 0%, #0e1626 100%);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: 0 24px 64px rgba(0,0,0,0.45);
        padding: 1.25rem 1.35rem 1.1rem;
        max-width: 720px;
        margin: 1rem auto 0.5rem;
      }

      .modal-head {
        display: flex;
        align-items: flex-start;
        gap: 0.85rem;
        margin-bottom: 1rem;
      }

      .shield {
        width: 42px; height: 42px; border-radius: 10px;
        background: linear-gradient(145deg, #2563eb, #1d4ed8);
        display: grid; place-items: center;
        box-shadow: 0 0 0 1px rgba(96,165,250,0.35), 0 8px 20px rgba(37,99,235,0.35);
        font-size: 1.25rem;
        flex-shrink: 0;
      }

      .title {
        margin: 0;
        font-size: 1.28rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text);
      }

      .subtitle {
        margin: 0.2rem 0 0;
        color: var(--muted);
        font-size: 0.92rem;
      }

      .info-box {
        border: 1px solid rgba(59,130,246,0.45);
        background: rgba(37,99,235,0.12);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: #cfe0ff;
        font-size: 0.92rem;
        margin: 0.4rem 0 1rem;
        line-height: 1.45;
      }

      .section-title {
        color: var(--accent-2);
        font-weight: 600;
        font-size: 1.02rem;
        margin: 0.2rem 0 0.75rem;
      }

      .feature-box {
        border: 1px solid var(--line);
        background: var(--panel-2);
        border-radius: 10px;
        padding: 0.95rem 1.05rem 0.85rem;
      }

      .feature-box h4 {
        margin: 0 0 0.55rem;
        color: var(--text);
        font-size: 0.95rem;
      }

      .feature-box ul {
        margin: 0;
        padding-left: 1.1rem;
        color: #d5e2f3;
        font-size: 0.9rem;
        line-height: 1.55;
      }

      .feature-box li { margin-bottom: 0.28rem; }

      .dns-note {
        color: var(--warn);
        font-size: 0.86rem;
        margin: 0.35rem 0 0.85rem;
        line-height: 1.4;
      }

      div[data-testid="stTabs"] button {
        color: var(--muted) !important;
        font-weight: 600;
      }

      div[data-testid="stTextInput"] input {
        background: #0c1422 !important;
        border: 1px solid var(--line) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
      }

      .status-pill {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(52,211,153,0.35);
        color: var(--ok);
        background: rgba(16,185,129,0.12);
      }

      .status-pill.missing {
        color: var(--warn);
        border-color: rgba(251,191,36,0.4);
        background: rgba(251,191,36,0.1);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if "mailbox_email" not in st.session_state:
    st.session_state.mailbox_email = RT["email"]
if "imap_host" not in st.session_state:
    st.session_state.imap_host = RT["imap_host"]
if "imap_port" not in st.session_state:
    st.session_state.imap_port = RT["imap_port"]
if "app_password" not in st.session_state:
    st.session_state.app_password = RT["app_password"]
if "saved" not in st.session_state:
    st.session_state.saved = False

password_set = bool(st.session_state.app_password.strip())
email_display = st.session_state.mailbox_email or "(set MAILBOX_EMAIL)"
domain_display = RT["domain"] or "(set GODADDY_DOMAIN)"

st.markdown(
    f"""
    <div class="modal">
      <div class="modal-head">
        <div class="shield">🛡️</div>
        <div>
          <p class="title">{CFG["title"]}</p>
          <p class="subtitle">{CFG["subtitle"]}</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_mail, tab_dns, tab_overview = st.tabs(
    ["📬 Mailbox & Credentials", "🗂️ DNS & Domain Records", "🧬 System Overview"]
)

with tab_mail:
    st.markdown(
        f"""
        <div class="info-box">
          <strong>Target Mailbox Configuration.</strong>
          This workspace syncs and organizes email for
          <code>{email_display}</code> ({RT["organization"]}).
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.text_input("Target Email Address", key="mailbox_email")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.text_input("IMAP Host Server", key="imap_host")
    with c2:
        st.text_input("IMAP Port", key="imap_port")
    st.text_input(
        "App Password / Auth Key",
        key="app_password",
        type="password",
        placeholder="Enter Workspace App Password...",
        help=MAIL["auth_note"],
    )

    if password_set:
        st.markdown(
            '<span class="status-pill">App password loaded from env</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-pill missing">App password missing — set MAILBOX_APP_PASSWORD</span>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Create one in Microsoft 365 / Entra: Security info → App passwords "
            "(MFA required). Paste it into `.env` as `MAILBOX_APP_PASSWORD=...` "
            "or enter it above and click Save Configuration."
        )

with tab_dns:
    st.markdown(
        f'<p class="section-title">DNS for <code>{domain_display}</code></p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="dns-note">⚠️ {DNS["provider_note"]}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("**MX RECORDS**")
    st.dataframe(
        [
            {
                "Priority": DNS["mx"][0]["priority"],
                "Host": DNS["mx"][0]["host"],
                "Points To": RT["mx_target"],
            }
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**SPF RECORD (TXT)**")
    st.code(f"Name: {DNS['spf']['name']}\nValue: {DNS['spf']['value']}", language=None)
    st.caption(DNS["spf"]["action"])

    st.markdown("**DMARC RECORD (TXT)**")
    st.code(f"Name: {DNS['dmarc']['name']}\nValue: {RT['dmarc']}", language=None)

    st.markdown("**Supporting Microsoft 365 records (already on GoDaddy)**")
    st.dataframe(RT["supporting"], use_container_width=True, hide_index=True)

with tab_overview:
    st.markdown(
        f'<p class="section-title">{OVERVIEW["heading"]}</p>',
        unsafe_allow_html=True,
    )
    items = "".join(f"<li>{feat}</li>" for feat in RT["features"])
    st.markdown(
        f"""
        <div class="feature-box">
          <h4>✅ Configured Features:</h4>
          <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
left, right = st.columns([1, 1])
with left:
    if st.button("Cancel", use_container_width=True):
        st.session_state.saved = False
        st.info("No changes saved.")
with right:
    if st.button("Save Configuration", type="primary", use_container_width=True):
        export = {
            "email_set": bool(st.session_state.mailbox_email.strip()),
            "imap_host": st.session_state.imap_host.strip(),
            "imap_port": int(st.session_state.imap_port or 993),
            "app_password_set": bool(st.session_state.app_password.strip()),
            "domain_set": bool(RT["domain"]),
            "dns": {
                "mx_points_to": RT["mx_target"],
                "spf": DNS["spf"]["value"],
                "dmarc": RT["dmarc"],
            },
        }
        out = ROOT / "config" / "mailbox_runtime_state.json"
        out.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")
        st.session_state.saved = True
        if not st.session_state.app_password.strip():
            st.warning(
                "Configuration saved without an app password. "
                "Set MAILBOX_APP_PASSWORD in `.env` before IMAP sync will work."
            )
        else:
            st.success(
                "Configuration saved (password kept in session/env only, not written to disk)."
            )

st.caption(
    f"Source of truth: `{CONFIG_PATH.relative_to(ROOT)}` · "
    "Secrets via env: MAILBOX_EMAIL, GODADDY_DOMAIN, MAILBOX_APP_PASSWORD"
)
