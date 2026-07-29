#!/usr/bin/env bash
# AI Capital App Launch Center hub (port 4720). Launch starts the meeting app on 3000.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export HUB_PORT="${HUB_PORT:-4720}"
export MEETING_PORT="${MEETING_PORT:-3000}"
echo "App Launch Center → http://127.0.0.1:${HUB_PORT}/"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port "$HUB_PORT"
