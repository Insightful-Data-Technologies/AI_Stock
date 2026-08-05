"""
Legacy entry Claude referenced from the Content Studio stub:

  streamlit run app/gpt52_dashboard_app.py

Dash 52 is now the FastAPI hub on port 8502 with Content Studio fully migrated
(Writing, Translate, Articles, Create Text, Create MD Document, Image Creation,
Canva Studio, Keyboard Fix). Prefer:

  bash dash52/run.sh

Then open: http://127.0.0.1:8502/content-studio
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("AI Capital — Dash 52")
    print("Legacy Streamlit entry redirected to the migrated FastAPI Content Studio.")
    print("Starting http://127.0.0.1:8502/content-studio …")
    env = os.environ.copy()
    env["HUB_PORT"] = "8502"
    env["ORG_DATA_DIR"] = env.get("ORG_DATA_DIR", "/tmp/org_platform_data_dash52")
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app_launch_center.hub:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8502",
        ],
        cwd=str(ROOT),
        env=env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
