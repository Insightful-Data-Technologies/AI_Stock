#!/usr/bin/env bash
# Everything on port 4720: App Launch Center + Meeting 41 B + 1:1 + dashboards.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export HUB_PORT="${HUB_PORT:-4720}"
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_launch}"
mkdir -p "$ORG_DATA_DIR"
echo "All-in-one on http://127.0.0.1:${HUB_PORT}/"
echo "  Launch Center:  http://127.0.0.1:${HUB_PORT}/apps"
echo "  Meeting 41 B:   http://127.0.0.1:${HUB_PORT}/meeting-41b.html"
echo "  One on One:     http://127.0.0.1:${HUB_PORT}/meeting-simulation.html"
echo "  Dashboard:      http://127.0.0.1:${HUB_PORT}/dashboard"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port "$HUB_PORT"
