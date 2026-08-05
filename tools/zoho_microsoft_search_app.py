#!/usr/bin/env python3
"""
Streamlit app: read-only search for Microsoft-related emails in Zoho Mail.
Created by Chanan Zevin.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from zoho_microsoft_search import (  # noqa: E402
    DEFAULT_DAYS,
    DEFAULT_FOLDER,
    DEFAULT_HOST,
    DEFAULT_TERMS,
    find_microsoft_emails,
)

load_dotenv()

st.set_page_config(
    page_title="Zoho · Microsoft Email Search",
    page_icon="📬",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --ink: #1a2332;
        --muted: #5a6a7a;
        --line: #d8e0e8;
        --accent: #0b6e4f;
        --accent-soft: #e6f4ef;
        --surface: #f7f9fb;
        --warn: #8a4b08;
      }
      .hero {
        background:
          radial-gradient(1200px 400px at 10% -20%, #d4ebe3 0%, transparent 55%),
          linear-gradient(160deg, #f4f8fb 0%, #eef3f7 45%, #e8eef4 100%);
        border-bottom: 1px solid var(--line);
        padding: 1.4rem 1.6rem 1.2rem;
        margin: -1rem -1rem 1.25rem;
        border-radius: 0 0 12px 12px;
      }
      .brand {
        font-family: "Segoe UI", "Heebo", sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--ink);
        letter-spacing: -0.02em;
        margin: 0;
      }
      .tagline {
        color: var(--muted);
        font-size: 0.98rem;
        margin: 0.35rem 0 0;
        max-width: 42rem;
      }
      .badge-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.85rem; }
      .badge {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--accent);
        background: var(--accent-soft);
        border: 1px solid #b7d9c9;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
      }
      .metric-label { color: var(--muted); font-size: 0.8rem; }
      .rtl { direction: rtl; text-align: right; }
      div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
COPY = {
    "he": {
        "brand": "Zoho · חיפוש מיילים ממיקרוסופט",
        "tagline": "חיפוש לקריאה בלבד בתיבת Zoho Mail — מוצא הודעות ממיקרוסופט, Azure ו-Office 365. הסיסמה לא נשמרת.",
        "badge_ro": "קריאה בלבד",
        "badge_imap": "IMAP מאובטח",
        "badge_local": "ללא שמירת סיסמה",
        "sidebar": "הגדרות חיבור",
        "email": "כתובת Zoho",
        "password": "סיסמת אפליקציה של Zoho",
        "password_help": "השתמש בסיסמת אפליקציה מ-Zoho Mail, לא בסיסמת הכניסה הרגילה.",
        "host": "שרת IMAP",
        "folder": "תיקייה",
        "days": "ימים אחורה",
        "terms": "מילות חיפוש (מופרדות בפסיק)",
        "run": "חפש הודעות",
        "need_creds": "נא למלא כתובת דוא״ל וסיסמת אפליקציה.",
        "searching": "מחפש בתיבה…",
        "done": "נמצאו {n} הודעות תואמות",
        "none": "לא נמצאו הודעות תואמות בטווח שנבחר.",
        "error": "שגיאת חיבור או IMAP",
        "results": "תוצאות",
        "download": "הורד JSON",
        "from": "מאת",
        "subject": "נושא",
        "date": "תאריך",
        "terms_col": "מילים שזוהו",
        "snippet": "תקציר",
        "detail": "פרטי הודעה",
        "cli_hint": "CLI: python tools/zoho_microsoft_search.py --email you@domain.com",
        "how": "איך זה עובד",
        "how_body": (
            "1. צור סיסמת אפליקציה ב-Zoho Mail (Settings → Security → App Passwords).\n"
            "2. בחר שרת: `imap.zoho.com` או `imap.zoho.eu` לחשבון אירופי.\n"
            "3. החיפוש בוחר את התיקייה במצב readonly וסורק הודעות מהימים האחרונים.\n"
            "4. תוצאות מוצגות כאן וניתנות להורדה כ-JSON."
        ),
    },
    "en": {
        "brand": "Zoho · Microsoft Email Search",
        "tagline": "Read-only Zoho Mail search for Microsoft, Azure, and Office 365 messages. Your password is never stored.",
        "badge_ro": "Read-only",
        "badge_imap": "Secure IMAP",
        "badge_local": "No password storage",
        "sidebar": "Connection",
        "email": "Zoho email",
        "password": "Zoho app password",
        "password_help": "Use a Zoho Mail app password, not your regular login password.",
        "host": "IMAP host",
        "folder": "Folder",
        "days": "Days back",
        "terms": "Search terms (comma-separated)",
        "run": "Search emails",
        "need_creds": "Please enter email and app password.",
        "searching": "Searching mailbox…",
        "done": "Found {n} matching email(s)",
        "none": "No matching emails in the selected range.",
        "error": "Connection / IMAP error",
        "results": "Results",
        "download": "Download JSON",
        "from": "From",
        "subject": "Subject",
        "date": "Date",
        "terms_col": "Matched terms",
        "snippet": "Snippet",
        "detail": "Message detail",
        "cli_hint": "CLI: python tools/zoho_microsoft_search.py --email you@domain.com",
        "how": "How it works",
        "how_body": (
            "1. Create an app password in Zoho Mail (Settings → Security → App Passwords).\n"
            "2. Choose host: `imap.zoho.com`, or `imap.zoho.eu` for EU accounts.\n"
            "3. Search selects the folder read-only and scans recent messages.\n"
            "4. Results appear here and can be downloaded as JSON."
        ),
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "he")
    return COPY[lang][key]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
lang_col, _ = st.columns([1, 5])
with lang_col:
    lang = st.radio(
        "Language / שפה",
        options=["he", "en"],
        format_func=lambda x: "עברית" if x == "he" else "English",
        horizontal=True,
        label_visibility="collapsed",
    )
st.session_state["lang"] = lang
rtl_class = "rtl" if lang == "he" else ""

st.markdown(
    f"""
    <div class="hero {rtl_class}">
      <p class="brand">{t("brand")}</p>
      <p class="tagline">{t("tagline")}</p>
      <div class="badge-row">
        <span class="badge">{t("badge_ro")}</span>
        <span class="badge">{t("badge_imap")}</span>
        <span class="badge">{t("badge_local")}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar connection form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(t("sidebar"))
    default_email = os.getenv("ZOHO_EMAIL", "")
    default_host = os.getenv("ZOHO_IMAP_HOST", DEFAULT_HOST)

    email_addr = st.text_input(t("email"), value=default_email)
    password = st.text_input(
        t("password"),
        type="password",
        help=t("password_help"),
        value=os.getenv("ZOHO_APP_PASSWORD", ""),
    )
    host = st.selectbox(
        t("host"),
        options=[DEFAULT_HOST, "imap.zoho.eu", "imap.zoho.in"],
        index=(
            [DEFAULT_HOST, "imap.zoho.eu", "imap.zoho.in"].index(default_host)
            if default_host in (DEFAULT_HOST, "imap.zoho.eu", "imap.zoho.in")
            else 0
        ),
    )
    folder = st.text_input(t("folder"), value=DEFAULT_FOLDER)
    days = st.slider(t("days"), min_value=1, max_value=365, value=DEFAULT_DAYS)
    terms_raw = st.text_input(
        t("terms"),
        value=", ".join(DEFAULT_TERMS),
    )
    run = st.button(t("run"), type="primary", use_container_width=True)

with st.expander(t("how"), expanded=False):
    st.markdown(t("how_body"))
    st.caption(t("cli_hint"))

# ---------------------------------------------------------------------------
# Search action
# ---------------------------------------------------------------------------
if "results" not in st.session_state:
    st.session_state["results"] = []
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None

if run:
    if not email_addr.strip() or not password:
        st.warning(t("need_creds"))
    else:
        terms = [x.strip() for x in terms_raw.split(",") if x.strip()]
        progress_bar = st.progress(0, text=t("searching"))
        status_box = st.empty()

        def on_progress(current: int, total: int) -> None:
            if total <= 0:
                progress_bar.progress(1.0, text=t("searching"))
                return
            frac = min(current / total, 1.0)
            progress_bar.progress(frac, text=f"{t('searching')} {current}/{total}")

        try:
            results = find_microsoft_emails(
                email_addr.strip(),
                password,
                host=host,
                days=days,
                terms=terms,
                folder=folder.strip() or DEFAULT_FOLDER,
                progress=on_progress,
            )
            st.session_state["results"] = results
            st.session_state["last_error"] = None
            progress_bar.progress(1.0, text=t("done").format(n=len(results)))
            status_box.success(t("done").format(n=len(results)))
        except Exception as exc:  # noqa: BLE001 — surface IMAP/network errors in UI
            st.session_state["results"] = []
            st.session_state["last_error"] = str(exc)
            progress_bar.empty()
            status_box.error(f"{t('error')}: {exc}")

if st.session_state["last_error"] and not run:
    st.error(f"{t('error')}: {st.session_state['last_error']}")

results: list[dict[str, Any]] = st.session_state.get("results") or []

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
st.subheader(t("results"))

if not results:
    st.info(t("none"))
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Matches" if lang == "en" else "התאמות", len(results))
    latest = results[0].get("date") or "—"
    m2.metric(t("date"), str(latest)[:19] if latest else "—")
    m3.metric(t("host"), host)

    rows = [
        {
            t("date"): (r.get("date") or "")[:19],
            t("from"): r.get("from", ""),
            t("subject"): r.get("subject", ""),
            t("terms_col"): ", ".join(r.get("matched_terms") or []),
            t("snippet"): r.get("snippet", ""),
        }
        for r in results
    ]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "emails": results,
    }
    st.download_button(
        t("download"),
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="microsoft_emails.json",
        mime="application/json",
    )

    st.markdown(f"### {t('detail')}")
    labels = [
        f"{(r.get('date') or '')[:19]} · {r.get('subject') or '(no subject)'}"
        for r in results
    ]
    choice = st.selectbox(" ", options=range(len(results)), format_func=lambda i: labels[i])
    selected = results[choice]
    st.markdown(f"**{t('from')}:** {selected.get('from', '')}")
    st.markdown(f"**{t('subject')}:** {selected.get('subject', '')}")
    st.markdown(f"**{t('date')}:** {selected.get('date', '')}")
    st.markdown(f"**{t('terms_col')}:** {', '.join(selected.get('matched_terms') or [])}")
    st.text_area(
        t("snippet"),
        value=selected.get("body_preview") or selected.get("snippet") or "",
        height=220,
        disabled=True,
    )
