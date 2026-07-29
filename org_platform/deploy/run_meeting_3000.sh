#!/usr/bin/env bash
# Run the One on One / org meeting service on port 3000 (App Launch Center target).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_meeting_3000}"
export PORT="${PORT:-3000}"
mkdir -p "$ORG_DATA_DIR"
echo "Starting AI Agent Meeting Simulation on http://127.0.0.1:${PORT}/meeting-simulation.html"
exec python3 -m uvicorn org_platform.api.app:app --host 0.0.0.0 --port "$PORT"
