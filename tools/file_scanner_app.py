# File: C:/AI_Backtest_Dev/streamlit/file_scanner_app.py
"""
File: C:/AI_Backtest_Dev/streamlit/file_scanner_app.py

This Streamlit app scans filesystem folders that are
supplied from a DataFrame or SQL table and writes
the inventory into SQL tables (operational + history).
The SQL connection is read from environment (.env) by default,
with optional UI override (CSV/JSON) if needed.
All dynamic inputs come from environment, DataFrames, or SQL.
No files are written to local disk at any time.
Created by Chanan Zevin.
"""

# =========================
# Standard Library Imports
# =========================
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# =========================
# Third-Party Imports
# =========================
import pandas as pd  # type: ignore
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

# pylint: disable=too-many-locals, too-many-branches, too-many-statements


# ==========================================================
# Page Config
# ==========================================================
st.set_page_config(page_title="Folder Scanner (.env connection)", layout="wide")


# ==========================================================
# Top Bar with App Button
# ==========================================================
st.markdown(
    """
    <style>
      .topbar {display:flex; gap:12px; align-items:center; margin-bottom:12px;}
      .app-title {font-size:26px; font-weight:700;}
      .btn-plain > button {width:100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

topcol1, topcol2, topcol3 = st.columns([6, 2, 2])
with topcol1:
    st.markdown('<div class="app-title">Folder Scanner • Reads DB connection from .env</div>', unsafe_allow_html=True)
with topcol2:
    # "App" button requested for the dashboard header.
    if st.button("App", key="btn_app_header"):
        st.session_state["app_mode_enabled"] = True
with topcol3:
    # Quick action to jump to scan section when app is open.
    if st.button("Run Scan", key="btn_run_scan_header"):
        st.session_state["app_mode_enabled"] = True
        st.session_state["auto_scroll_to_scan"] = True


# ==========================================================
# App Intro / Gate
# ==========================================================
if "app_mode_enabled" not in st.session_state:
    st.session_state["app_mode_enabled"] = False

if not st.session_state["app_mode_enabled"]:
    st.markdown(
        """
        **Overview:**  
        Press **App** to open the scanner interface.  
        The app will use your `.env` database connection.  

        **What you can do:**  
        • Load folders from SQL or CSV.  
        • Scan non-recursive file lists.  
        • Save to operational and history tables.  
        """
    )
    st.button("Open App", key="btn_open_app_intro", on_click=lambda: st.session_state.update({"app_mode_enabled": True}))
    # Command line hint lives here as well.
    st.caption("Command:  streamlit run C:/AI_Backtest_Dev/streamlit/file_scanner_app.py")
    st.stop()


# ==========================================================
# Helpers — Connection
# ==========================================================
def _bool_from_env(v: Optional[str], default: bool = True) -> bool:
    """
    Convert environment string to boolean.
    Accepts: '1','true','yes','y','on' → True.
             '0','false','no','n','off' → False.
    Falls back to default if None/empty/unknown.
    """
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _safe_getenv(name: str) -> Optional[str]:
    """
    Get environment variable and strip whitespace.
    Returns None if empty after strip.
    """
    val = os.getenv(name)
    if val is None:
        return None
    val = val.strip()
    return val if val else None


def read_db_cfg_from_env() -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load environment variables from .env (if present) and
    construct a one-row DataFrame with required keys.

    Required:
      DB_SERVER, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_DRIVER

    Optional:
      DB_INSTANCE, DB_ENCRYPT, DB_TRUSTSERVERCERTIFICATE, DB_TIMEOUT, DB_DSN
    """
    try:
        load_dotenv()  # load .env if exists

        # Optional DSN path (preferred if provided)
        dsn = _safe_getenv("DB_DSN")

        env_map: Dict[str, Any] = {
            "server": _safe_getenv("DB_SERVER"),
            "instance": _safe_getenv("DB_INSTANCE"),  # optional
            "port": _safe_getenv("DB_PORT"),
            "database": _safe_getenv("DB_NAME"),
            "username": _safe_getenv("DB_USERNAME"),
            "password": _safe_getenv("DB_PASSWORD"),
            "driver": _safe_getenv("DB_DRIVER"),
            "encrypt": _bool_from_env(_safe_getenv("DB_ENCRYPT"), default=True),
            "trust_server_certificate": _bool_from_env(
                _safe_getenv("DB_TRUSTSERVERCERTIFICATE"), default=True
            ),
            "timeout": _safe_getenv("DB_TIMEOUT") or "30",
            "dsn": dsn,
        }

        # If DSN is provided, allow missing other pieces.
        if not dsn:
            required = ["server", "database", "username", "password", "driver", "port"]
            missing = [k for k in required if not env_map.get(k)]
            if missing:
                return None, f"Missing keys in .env: {missing}"

        df = pd.DataFrame([env_map])
        return df, None
    except Exception as e:  # pylint: disable=broad-except
        return None, f"Error reading .env: {e}"


def build_pyodbc_url_from_row(row: pd.Series) -> str:
    """
    Build SQLAlchemy URL for SQL Server via pyodbc.

    Supports both DSN-based and DSN-less connection.
    If row['dsn'] is present, uses:
      mssql+pyodbc:///?odbc_connect=DSN=...;...

    Otherwise builds:
      Driver={ODBC Driver 18 for SQL Server};
      Server=HOST[,PORT][\\INSTANCE];
      Database=DB;UID=USER;PWD=PASS;Encrypt=...;TrustServerCertificate=...;
      Connection Timeout=...;
    """
    # DSN path
    dsn = row.get("dsn")
    if pd.notna(dsn) and str(dsn).strip():
        odbc = (
            f"DSN={row['dsn']};"
            f"Database={row['database']};"
            f"UID={row['username']};"
            f"PWD={row['password']};"
            f"Encrypt={'yes' if bool(row['encrypt']) else 'no'};"
            f"TrustServerCertificate={'yes' if bool(row['trust_server_certificate']) else 'no'};"
            f"Connection Timeout={row.get('timeout', '30')};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"

    # DSN-less path
    server = str(row["server"])
    instance = str(row.get("instance") or "").strip()
    port = str(row["port"])

    # Compose server, allowing either host, host,port, or host\instance,port
    server_part = server
    if instance:
        server_part = f"{server}\\{instance}"

    odbc = (
        f"Driver={{{row['driver']}}};"
        f"Server={server_part},{port};"
        f"Database={row['database']};"
        f"UID={row['username']};"
        f"PWD={row['password']};"
        f"Encrypt={'yes' if bool(row['encrypt']) else 'no'};"
        f"TrustServerCertificate={'yes' if bool(row['trust_server_certificate']) else 'no'};"
        f"Connection Timeout={row.get('timeout', '30')};"
    )
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


def connect_engine_from_df(db_cfg_df: pd.DataFrame) -> Tuple[Optional[Engine], Optional[str]]:
    """
    Create an Engine from a one-row DataFrame.
    Returns (engine, error_message).
    """
    if len(db_cfg_df) != 1:
        return None, "DB config must contain exactly one row."

    row = db_cfg_df.iloc[0]
    try:
        url = build_pyodbc_url_from_row(row)
        engine = create_engine(url, fast_executemany=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine, None
    except SQLAlchemyError as e:
        return None, f"SQL connection error: {e}"
    except Exception as e:  # pylint: disable=broad-except
        return None, f"Unexpected connection error: {e}"


@st.cache_data(show_spinner=False)
def list_tables(_engine: Engine) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Return a list of tables via INFORMATION_SCHEMA.
    The underscore in ``_engine`` prevents Streamlit from attempting to
    hash the SQLAlchemy engine when caching.
    """
    try:
        q = """
            SELECT TABLE_SCHEMA AS [schema],
                   TABLE_NAME   AS [table]
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME;
        """
        df = pd.read_sql(q, con=_engine)
        return df, None
    except Exception as e:  # pylint: disable=broad-except
        return pd.DataFrame(), f"Table listing error: {e}"


# ==========================================================
# Helpers — Folders Scan
# ==========================================================
def validate_folders_df(folders_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Expected columns:
      - folder_path (str)
      - is_active (bool or 0/1)
    """
    required = ["folder_path", "is_active"]
    missing = [c for c in required if c not in folders_df.columns]
    if missing:
        return None, f"Missing folders columns: {missing}"

    df = folders_df.copy()
    if df["is_active"].dtype != bool:
        df["is_active"] = df["is_active"].apply(lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
    df["folder_path"] = df["folder_path"].astype(str).str.strip()
    df = df[df["folder_path"] != ""].reset_index(drop=True)

    if df.empty:
        return None, "Folders DataFrame is empty after validation."

    return df, None


def scan_single_folder(folder: str) -> pd.DataFrame:
    """
    Non-recursive scan of a folder; return file metadata.
    """
    records = []
    base = Path(folder)

    if not base.exists() or not base.is_dir():
        return pd.DataFrame(
            [{"folder": folder, "filename": None, "size_bytes": None, "modified_utc": None, "status": "NOT_FOUND"}]
        )

    try:
        for entry in os.scandir(base):
            if not entry.is_file():
                continue
            try:
                stat = entry.stat()
                records.append(
                    {
                        "folder": str(base),
                        "filename": entry.name,
                        "size_bytes": int(stat.st_size),
                        "modified_utc": datetime.utcfromtimestamp(stat.st_mtime),
                        "status": "OK",
                    }
                )
            except Exception:  # pylint: disable=broad-except
                records.append(
                    {
                        "folder": str(base),
                        "filename": entry.name,
                        "size_bytes": None,
                        "modified_utc": None,
                        "status": "ERROR_READING_FILE",
                    }
                )
    except PermissionError:
        return pd.DataFrame(
            [{"folder": folder, "filename": None, "size_bytes": None, "modified_utc": None, "status": "NO_PERMISSION"}]
        )
    except FileNotFoundError:
        return pd.DataFrame(
            [{"folder": folder, "filename": None, "size_bytes": None, "modified_utc": None, "status": "NOT_FOUND"}]
        )
    except Exception:  # pylint: disable=broad-except
        return pd.DataFrame(
            [{"folder": folder, "filename": None, "size_bytes": None, "modified_utc": None, "status": "UNKNOWN_ERROR"}]
        )

    if not records:
        return pd.DataFrame(
            [{"folder": folder, "filename": None, "size_bytes": 0, "modified_utc": None, "status": "EMPTY_FOLDER"}]
        )

    return pd.DataFrame.from_records(records)


def scan_folders(folders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Scan all active folders and combine results.
    """
    results = []
    for _, row in folders_df.iterrows():
        if not bool(row["is_active"]):
            continue
        folder = str(row["folder_path"])
        df_folder = scan_single_folder(folder)
        results.append(df_folder)

    if not results:
        return pd.DataFrame(columns=["folder", "filename", "size_bytes", "modified_utc", "status"])

    combined = pd.concat(results, axis=0, ignore_index=True)
    combined.insert(0, "run_utc", datetime.utcnow())
    return combined


def save_df_to_sql(
    engine: Engine,
    df: pd.DataFrame,
    table_name_operational: str,
    table_name_history: str,
) -> Tuple[bool, Optional[str]]:
    """
    Save results into operational (truncate+insert) and history (append).
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {table_name_operational}"))
            # Use SQLAlchemy Connection with pandas to_sql (pandas 2.x + SA 2.x compatible)
            df.to_sql(table_name_operational, con=conn, if_exists="append", index=False)
            df.to_sql(table_name_history, con=conn, if_exists="append", index=False)
        return True, None
    except SQLAlchemyError as e:
        return False, f"SQL save error: {e}"
    except Exception as e:  # pylint: disable=broad-except
        return False, f"Unexpected save error: {e}"


def log_event(
    engine: Optional[Engine],
    log_table: Optional[str],
    level: str,
    message: str,
    context: Optional[dict] = None,
) -> None:
    """
    Insert a log record into a SQL log table (best-effort).
    """
    if engine is None or not log_table:
        return
    try:
        payload = {
            "event_utc": datetime.utcnow(),
            "level": level,
            "message": message,
            "context_json": pd.Series([context]).to_json(orient="records") if context else None,
        }
        df_log = pd.DataFrame([payload])
        with engine.begin() as conn:
            df_log.to_sql(log_table, con=conn, if_exists="append", index=False)
    except Exception:
        pass


# ==========================================================
# Step 1 — Database connection (.env → auto)
# ==========================================================
st.subheader("Step 1 — Database connection (.env → auto)")

db_cfg_df_env, env_err = read_db_cfg_from_env()
engine: Optional[Engine] = None
db_err: Optional[str] = None

def _mask_df(df: pd.DataFrame) -> pd.DataFrame:
    m = df.copy()
    if "password" in m.columns:
        m.loc[:, "password"] = m["password"].apply(lambda x: "***" if pd.notna(x) and str(x) else x)
    return m

if db_cfg_df_env is not None and env_err is None:
    st.caption("Loaded DB configuration from .env")
    st.dataframe(_mask_df(db_cfg_df_env), use_container_width=True)
    engine, db_err = connect_engine_from_df(db_cfg_df_env)
else:
    st.warning(env_err or "No .env found or missing keys.")
    db_err = "No engine yet."

with st.expander("Override connection (CSV/JSON) — optional"):
    tab_upload, tab_json = st.tabs(["Upload CSV", "Paste JSON"])
    db_cfg_df_override: Optional[pd.DataFrame] = None

    with tab_upload:
        st.markdown("Upload a one-row CSV with columns: server,database,username,password,driver,port[,instance,encrypt,trust_server_certificate,timeout,dsn]")
        file = st.file_uploader("Upload DB config CSV", type=["csv"], key="db_csv")
        if file:
            try:
                temp_df = pd.read_csv(file)
                db_cfg_df_override = temp_df.copy()
                st.dataframe(_mask_df(db_cfg_df_override), use_container_width=True)
            except Exception as e:  # pylint: disable=broad-except
                st.error(f"CSV read error: {e}")

    with tab_json:
        st.markdown("Paste JSON with required keys.")
        sample = (
            '{\n'
            '  "server": "LAPTOP-XXXX",\n'
            '  "database": "AI_Stocks",\n'
            '  "username": "sa2",\n'
            '  "password": "*****",\n'
            '  "driver": "ODBC Driver 18 for SQL Server",\n'
            '  "port": "1433",\n'
            '  "instance": "",\n'
            '  "encrypt": true,\n'
            '  "trust_server_certificate": true,\n'
            '  "timeout": "30"\n'
            '}'
        )
        json_text = st.text_area("DB config JSON", value=sample, height=200, key="db_json")
        if json_text.strip() and st.button("Use JSON override"):
            try:
                df_json = pd.read_json(pd.io.common.StringIO(json_text), typ="series").to_frame().T
                db_cfg_df_override = df_json
                st.dataframe(_mask_df(db_cfg_df_override), use_container_width=True)
            except Exception as e:  # pylint: disable=broad-except
                st.error(f"Invalid JSON: {e}")

    if db_cfg_df_override is not None:
        engine, db_err = connect_engine_from_df(db_cfg_df_override)

row1_col1, row1_col2, row1_col3 = st.columns([1.2, 1, 1])
with row1_col1:
    if engine and not db_err:
        st.success("Connected successfully.")
    else:
        st.error(db_err or "Not connected.")

with row1_col2:
    if engine and st.button("Connect / Refresh Tables"):
        tbl_df, terr = list_tables(engine)
        if terr:
            st.error(terr)
        else:
            st.session_state["__tables_cache__"] = tbl_df
            st.dataframe(tbl_df, use_container_width=True)

with row1_col3:
    if st.button("Clear Output"):
        for key in ["__tables_cache__", "auto_scroll_to_scan"]:
            if key in st.session_state:
                del st.session_state[key]
        # Streamlit >=1.30 uses st.rerun(); keep compatibility with older versions
        try:
            st.rerun()
        except Exception:
            try:
                st.experimental_rerun()
            except Exception:
                pass


# ==========================================================
# Step 2 — Provide folders list (DataFrame or SQL)
# ===============================================
