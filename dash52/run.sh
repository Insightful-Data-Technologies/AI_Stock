#!/usr/bin/env bash
# AI Capital — Dash 52 on port 8502 (Content Studio fully migrated).
set -euo pipefail
cd "$(dirname "$0")/.."
export HUB_PORT=8502
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_dash52}"
mkdir -p "$ORG_DATA_DIR"
echo "Dash 52 → http://127.0.0.1:8502/content-studio"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port 8502
