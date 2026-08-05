#!/usr/bin/env bash
# AI Capital — Dash 52 / Content Studio on 8502 (same codebase as 4720).
# Replaces the old Claude half-migration that showed "NOT YET MIGRATED".
set -euo pipefail
cd "$(dirname "$0")/.."
export HUB_PORT=8502
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_dash52}"
mkdir -p "$ORG_DATA_DIR"
echo "Content Studio → http://127.0.0.1:8502/content-studio"
echo "Dash 52         → http://127.0.0.1:8502/dash52"
echo "Primary hub     → http://127.0.0.1:4720/content-studio"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port 8502
