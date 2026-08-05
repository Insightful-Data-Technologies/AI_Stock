#!/usr/bin/env bash
# Button Launch Center on 4720 and/or 4600 (no terminal needed for the user).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export ORG_DATA_DIR="${ORG_DATA_DIR:-/tmp/org_platform_data_launch}"
mkdir -p "$ORG_DATA_DIR"

PORTS="${HUB_PORTS:-${HUB_PORT:-4720,4600}}"
IFS=',' read -r -a PORT_LIST <<< "$PORTS"

pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

for port in "${PORT_LIST[@]}"; do
  port="$(echo "$port" | tr -d '[:space:]')"
  [[ -z "$port" ]] && continue
  echo "Buttons ready → http://127.0.0.1:${port}/"
  HUB_PORT="$port" python3 -m uvicorn app_launch_center.hub:app --host 0.0.0.0 --port "$port" &
  pids+=("$!")
done

wait
