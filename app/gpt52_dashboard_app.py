"""
Legacy entry formerly referenced as:

  streamlit run app/gpt52_dashboard_app.py

Dash 52 now lives on the Launch Center hub (primary **4720**):

  http://127.0.0.1:4720/dash52
  http://127.0.0.1:4720/content-studio

This script starts the same FastAPI hub. Prefer:

  bash app_launch_center/run_hub.sh
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    port = os.environ.get("HUB_PORT", "4720")
    print("AI Capital — Dash 52")
    print("Legacy Streamlit entry redirected to the Launch Center hub.")
    print(f"Starting http://127.0.0.1:{port}/dash52 …")
    env = os.environ.copy()
    env["HUB_PORT"] = str(port)
    env["ORG_DATA_DIR"] = env.get("ORG_DATA_DIR", "/tmp/org_platform_data_launch")
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app_launch_center.hub:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
