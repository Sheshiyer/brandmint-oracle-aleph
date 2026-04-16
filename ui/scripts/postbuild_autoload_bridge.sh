#!/usr/bin/env bash
set -euo pipefail

if [[ "${CI:-}" == "true" ]]; then
  echo "[tauri:build:fresh] CI detected, skipping app auto-launch."
  exit 0
fi

UI_DIR="$(cd "$(dirname "$0")/.." && pwd)"

case "$(uname -m)" in
  arm64|aarch64)
    TARGET_TRIPLE="aarch64-apple-darwin"
    ;;
  x86_64)
    TARGET_TRIPLE="x86_64-apple-darwin"
    ;;
  *)
    echo "[tauri:build:fresh] Unsupported macOS arch: $(uname -m)" >&2
    exit 1
    ;;
esac

APP_BUNDLE="${UI_DIR}/src-tauri/target/${TARGET_TRIPLE}/release/bundle/macos/Brandmint.app"
APP_EXECUTABLE="${APP_BUNDLE}/Contents/MacOS/brandmint-app"

if [[ ! -d "${APP_BUNDLE}" ]]; then
  echo "[tauri:build:fresh] App bundle not found at ${APP_BUNDLE}" >&2
  exit 1
fi

echo "[tauri:build:fresh] Launching ${APP_BUNDLE} (bridge autoload is triggered during app startup)."
if open "${APP_BUNDLE}"; then
  exit 0
fi

echo "[tauri:build:fresh] LaunchServices open failed, attempting direct executable launch."
if [[ ! -x "${APP_EXECUTABLE}" ]]; then
  echo "[tauri:build:fresh] Executable not found at ${APP_EXECUTABLE}" >&2
  exit 1
fi

nohup "${APP_EXECUTABLE}" >/tmp/brandmint-postbuild-launch.log 2>&1 &
echo "[tauri:build:fresh] Started ${APP_EXECUTABLE} in background (logs: /tmp/brandmint-postbuild-launch.log)."
