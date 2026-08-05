#!/usr/bin/env bash
# Site Editor CMS on the familiar local port 8511 (same app as Launch Center hub).
set -euo pipefail
cd "$(dirname "$0")/.."
export HUB_PORT=8511
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_launch}"
exec python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port 8511
