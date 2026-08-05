#!/usr/bin/env bash
# Run Zoho Microsoft email search Streamlit app on port 4720.
set -euo pipefail
cd "$(dirname "$0")/.."
exec streamlit run tools/zoho_microsoft_search_app.py \
  --server.headless true \
  --server.port "${ZOHO_SEARCH_PORT:-4720}" \
  --browser.gatherUsageStats false
