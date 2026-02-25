#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[ui-stack] starting backend bridge on 4191..."
python3 scripts/ui_backend_bridge.py &
BRIDGE_PID=$!

cleanup() {
  echo "[ui-stack] stopping backend bridge..."
  kill "$BRIDGE_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "[ui-stack] starting frontend on 4188..."
npm run ui:guard
