#!/usr/bin/env bash
# Launch Mailbox & Domain Configuration UI (default port 4721).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${MAILBOX_CONFIG_PORT:-4721}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
exec python3 -m streamlit run tools/mailbox_domain_config_app.py \
  --server.port "$PORT" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
