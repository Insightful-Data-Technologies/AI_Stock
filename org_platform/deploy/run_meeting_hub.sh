#!/usr/bin/env bash
# All meeting + Launch Center services on a single port (default 4720).
set -euo pipefail
cd /workspace
export PYTHONPATH=/workspace
export HUB_PORT="${HUB_PORT:-4720}"
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data}"
mkdir -p "$ORG_DATA_DIR"
echo "Serving everything on http://127.0.0.1:${HUB_PORT}/"
echo "  /apps                  App Launch Center"
echo "  /meeting-41b.html      Meeting 41 B · Visuals"
echo "  /meeting-simulation.html  Ultra Agent 1:1"
echo "  /dashboard             General dashboard"
exec bash /workspace/app_launch_center/run_hub.sh
