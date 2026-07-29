#!/usr/bin/env bash
set -euo pipefail
cd /workspace
export PYTHONPATH=/workspace
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data}"
export PORT="${PORT:-8080}"
mkdir -p "$ORG_DATA_DIR"
exec python3 -m uvicorn org_platform.api.app:app --host 0.0.0.0 --port "$PORT"
