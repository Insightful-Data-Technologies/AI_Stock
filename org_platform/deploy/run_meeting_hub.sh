#!/usr/bin/env bash
# Serve App Launch Center on hub port 4720 and org meeting platform on 3000.
set -euo pipefail
cd /workspace
export PYTHONPATH=/workspace
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data}"
mkdir -p "$ORG_DATA_DIR"

MEETING_PORT="${MEETING_PORT:-3000}"
HUB_PORT="${HUB_PORT:-4720}"

python3 -m uvicorn org_platform.api.app:app --host 127.0.0.1 --port "$MEETING_PORT" &
MEETING_PID=$!

python3 - <<'PY' &
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os

root = Path("/workspace/app_launch_center/static")
os.chdir(root)
port = int(os.environ.get("HUB_PORT", "4720"))
httpd = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
print(f"App Launch Center on http://127.0.0.1:{port}/", flush=True)
httpd.serve_forever()
PY
HUB_PID=$!

cleanup() {
  kill "$MEETING_PID" "$HUB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Meeting simulation: http://127.0.0.1:${MEETING_PORT}/meeting-simulation.html"
echo "App Launch Center:  http://127.0.0.1:${HUB_PORT}/"
wait
