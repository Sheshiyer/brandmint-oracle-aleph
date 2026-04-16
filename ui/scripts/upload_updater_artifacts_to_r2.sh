#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_UPDATE_PRIMARY_BASE_URL="https://brandmintupdates.thoughtseed.space"
DEFAULT_UPDATE_FALLBACK_BASE_URL="https://pub-1a0540bfbd114ca7aa86f0abdfbe154f.r2.dev"

bundle_root=""
channel="${BRANDMINT_UPDATE_CHANNEL:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle-root)
      bundle_root="$2"
      shift 2
      ;;
    --channel)
      channel="$2"
      shift 2
      ;;
    *)
      echo "[tauri:upload] Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${channel}" ]]; then
  if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]]; then
    channel="stable"
  else
    channel="dev"
  fi
fi

bucket="${BRANDMINT_UPDATE_BUCKET:-brandmint-updater}"
platform_key="${BRANDMINT_UPDATE_PLATFORM:-${BRANDMINT_UPDATER_PLATFORM:-darwin-aarch64}}"
base_url_root="${BRANDMINT_UPDATE_PRIMARY_BASE_URL:-${BRANDMINT_UPDATE_BASE_URL:-${DEFAULT_UPDATE_PRIMARY_BASE_URL}}}"
base_url="${base_url_root%/}/${channel}"

if [[ -z "${bundle_root}" ]]; then
  bundle_root="${UI_DIR}/src-tauri/target/release/bundle"
  if [[ ! -d "${bundle_root}" ]]; then
    case "$(uname -m)" in
      arm64|aarch64)
        inferred_target="aarch64-apple-darwin"
        ;;
      x86_64)
        inferred_target="x86_64-apple-darwin"
        ;;
      *)
        inferred_target=""
        ;;
    esac
    if [[ -n "${inferred_target}" ]]; then
      bundle_root="${UI_DIR}/src-tauri/target/${inferred_target}/release/bundle"
    fi
  fi
fi

if [[ ! -d "${bundle_root}" ]]; then
  echo "[tauri:upload] Bundle root not found: ${bundle_root}" >&2
  exit 1
fi

archive_path="$(find "${bundle_root}" -type f -name '*.app.tar.gz' | head -n 1)"
signature_path="$(find "${bundle_root}" -type f -name '*.app.tar.gz.sig' | head -n 1)"

if [[ -z "${archive_path}" || -z "${signature_path}" ]]; then
  echo "[tauri:upload] Signed updater artifacts were not found under ${bundle_root}" >&2
  exit 1
fi

version="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' \
    "${UI_DIR}/src-tauri/tauri.conf.json"
)"
manifest_path="${bundle_root}/latest.json"

python3 "${SCRIPT_DIR}/generate_updater_manifest.py" \
  --archive "${archive_path}" \
  --signature "${signature_path}" \
  --version "${version}" \
  --base-url "${base_url}" \
  --output "${manifest_path}" \
  --platform "${platform_key}"

if command -v wrangler >/dev/null 2>&1; then
  wrangler_cmd=(wrangler)
else
  wrangler_cmd=(npx --yes wrangler@4.83.0)
fi

"${wrangler_cmd[@]}" r2 object put "${bucket}/${channel}/$(basename "${archive_path}")" \
  --file "${archive_path}" \
  --content-type application/gzip \
  --remote

"${wrangler_cmd[@]}" r2 object put "${bucket}/${channel}/$(basename "${signature_path}")" \
  --file "${signature_path}" \
  --content-type text/plain \
  --cache-control no-cache \
  --remote

"${wrangler_cmd[@]}" r2 object put "${bucket}/${channel}/latest.json" \
  --file "${manifest_path}" \
  --content-type application/json \
  --cache-control no-store \
  --remote

echo "[tauri:upload] Uploaded OTA artifacts to bucket '${bucket}' channel '${channel}'"
echo "[tauri:upload] Manifest URL: ${base_url}/latest.json"
