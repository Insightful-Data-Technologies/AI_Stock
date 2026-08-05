"""Site Editor CMS — DB connection helpers (ODBC 18 safe, no crash on failure)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote_plus

from org_platform.publish.env_loader import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def build_odbc_connect_string() -> str:
    """
    Build a Driver-18-safe ODBC connect string.

    Fixes common failure modes seen on :8511:
    - missing Encrypt= (Driver 18)
    - invalid / empty attributes
    - brace-wrapping the driver name correctly once
    """
    raw = _env("DB_CONN_STR")
    driver = _env("DB_DRIVER")
    # Strip accidental outer braces from env value.
    driver = driver.strip().strip("{}")
    server = _env("DB_SERVER")
    port = _env("DB_PORT", "1433")
    database = _env("DB_NAME")
    user = _env("DB_USERNAME")
    password = _env("DB_PASSWORD")

    if not driver:
        raise RuntimeError("DB_DRIVER is not set")

    if raw and "Driver=" in raw and "UID=" in raw:
        # Normalize a provided string instead of trusting it blindly.
        parts: Dict[str, str] = {}
        for chunk in raw.split(";"):
            chunk = chunk.strip()
            if not chunk or "=" not in chunk:
                continue
            key, val = chunk.split("=", 1)
            key = key.strip()
            val = val.strip()
            if not key:
                continue
            parts[key.lower()] = val
        # Prefer discrete env fields when present.
        if server:
            parts["server"] = f"{server},{port}" if port and "," not in server else server
        if database:
            parts["database"] = database
        if user:
            parts["uid"] = user
        if password:
            parts["pwd"] = password
        parts["driver"] = "{" + driver + "}"
        parts["encrypt"] = parts.get("encrypt") or "yes"
        parts.setdefault("trustservercertificate", "yes")
        parts.setdefault("connection timeout", "5")
        ordered = [
            ("Driver", parts["driver"]),
            ("Server", parts.get("server", "")),
            ("Database", parts.get("database", "")),
            ("UID", parts.get("uid", "")),
            ("PWD", parts.get("pwd", "")),
            ("Encrypt", parts.get("encrypt", "yes")),
            ("TrustServerCertificate", parts.get("trustservercertificate", "yes")),
            ("Connection Timeout", parts.get("connection timeout", "5")),
        ]
        return ";".join(f"{k}={v}" for k, v in ordered if v != "") + ";"

    if not (server and database and user and password):
        raise RuntimeError("Database env is incomplete (DB_SERVER/DB_NAME/DB_USERNAME/DB_PASSWORD)")

    return (
        f"Driver={{{driver}}};"
        f"Server={server},{port};"
        f"Database={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=5;"
    )


def sqlalchemy_url() -> str:
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(build_odbc_connect_string())}"


def probe_database() -> Dict[str, Any]:
    """
    Probe SQL Server. Never raise — returns structured status for the UI.
    Falls back to local workspace store when SQL is unreachable / login fails.
    """
    try:
        odbc = build_odbc_connect_string()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "mode": "local",
            "error": str(exc),
            "hint": "Fill DB_* in .env. Site Editor continues on local store.",
        }

    # Masked summary for UI (no password).
    masked = []
    for chunk in odbc.split(";"):
        if not chunk or "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        if k.lower() in {"pwd", "password"}:
            masked.append(f"{k}=***")
        else:
            masked.append(f"{k}={v}")
    summary = ";".join(masked)

    try:
        import pyodbc  # type: ignore
    except Exception:
        return {
            "ok": False,
            "mode": "local",
            "error": "pyodbc is not installed in this environment",
            "connection": summary,
            "hint": "Install the SQL Server ODBC driver + pyodbc on the Windows host, or use local store.",
        }

    try:
        conn = pyodbc.connect(odbc, timeout=5)
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
        finally:
            conn.close()
        return {
            "ok": True,
            "mode": "sqlserver",
            "connection": summary,
            "message": "SQL Server connected",
        }
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        hint = "Check sa2 password / SQL auth on the host."
        if "18456" in msg or "Login failed" in msg:
            hint = (
                "Login failed for sa2 — wrong password, or SQL Server auth disabled. "
                "Site Editor stays usable on local store."
            )
        elif "Invalid connection string attribute" in msg:
            hint = (
                "ODBC string had an invalid attribute — rebuilt with Encrypt and "
                "TrustServerCertificate for the configured SQL Server driver."
            )
        return {
            "ok": False,
            "mode": "local",
            "error": msg.split("(Background on this error")[0].strip(),
            "connection": summary,
            "hint": hint,
        }


def get_engine() -> Tuple[Optional[Any], Optional[str]]:
    status = probe_database()
    if not status.get("ok"):
        return None, status.get("error") or "SQL unavailable"
    try:
        from sqlalchemy import create_engine

        engine = create_engine(sqlalchemy_url(), pool_pre_ping=True)
        return engine, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
