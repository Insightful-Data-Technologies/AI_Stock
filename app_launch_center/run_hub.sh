#!/usr/bin/env bash
# AI Capital App Launch Center hub (port 4720).
# Launch prefers meeting port 3000; if busy, falls back to 4050 (then 4051…).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export HUB_PORT="${HUB_PORT:-4720}"
export MEETING_PORTS="${MEETING_PORTS:-3000,4050,4051,4052,4060}"
echo "App Launch Center → http://127.0.0.1:${HUB_PORT}/"
echo "Meeting ports preference: ${MEETING_PORTS}"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port "$HUB_PORT"
