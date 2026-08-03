#!/usr/bin/env bash
# Run the full meeting + Launch Center stack (defaults to port 4720).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_meeting_4720}"
export HUB_PORT="${HUB_PORT:-${PORT:-4720}}"
export PORT="$HUB_PORT"
mkdir -p "$ORG_DATA_DIR"
echo "Starting all meetings on http://127.0.0.1:${HUB_PORT}/"
echo "  Meeting 41 B → http://127.0.0.1:${HUB_PORT}/meeting-41b.html"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port "$HUB_PORT"
