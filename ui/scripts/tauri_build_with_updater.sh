#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCAL_SIGNING_KEY="${TAURI_LOCAL_SIGNING_KEY_PATH:-${HOME}/.tauri/brandmint.key}"
LOCAL_SIGNING_KEY_PASSWORD_FILE="${TAURI_LOCAL_SIGNING_KEY_PASSWORD_PATH:-${HOME}/.tauri/brandmint.key.password}"
DEFAULT_UPDATE_PRIMARY_BASE_URL="https://brandmintupdates.thoughtseed.space"
DEFAULT_UPDATE_FALLBACK_BASE_URL="https://pub-1a0540bfbd114ca7aa86f0abdfbe154f.r2.dev"

build_args=("$@")
target_triple=""
for ((i = 0; i < ${#build_args[@]}; i += 1)); do
  if [[ "${build_args[$i]}" == "--target" ]] && (( i + 1 < ${#build_args[@]} )); then
    target_triple="${build_args[$((i + 1))]}"
    break
  fi
done

if [[ -z "${BRANDMINT_UPDATE_CHANNEL:-}" ]]; then
  if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]]; then
    export BRANDMINT_UPDATE_CHANNEL="stable"
  else
    export BRANDMINT_UPDATE_CHANNEL="dev"
  fi
fi

export BRANDMINT_UPDATE_PRIMARY_BASE_URL="${BRANDMINT_UPDATE_PRIMARY_BASE_URL:-${DEFAULT_UPDATE_PRIMARY_BASE_URL}}"
export BRANDMINT_UPDATE_BASE_URL="${BRANDMINT_UPDATE_BASE_URL:-${DEFAULT_UPDATE_FALLBACK_BASE_URL}}"
export BRANDMINT_UPDATE_BUCKET="${BRANDMINT_UPDATE_BUCKET:-brandmint-updater}"

if [[ -z "${TAURI_SIGNING_PRIVATE_KEY:-}" ]] && [[ -f "${LOCAL_SIGNING_KEY}" ]]; then
  export TAURI_SIGNING_PRIVATE_KEY="$(cat "${LOCAL_SIGNING_KEY}")"
  echo "[tauri:build] Using local updater signing key from ${LOCAL_SIGNING_KEY}"
fi

if [[ -z "${TAURI_SIGNING_PRIVATE_KEY_PASSWORD:-}" ]] && [[ -f "${LOCAL_SIGNING_KEY_PASSWORD_FILE}" ]]; then
  export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="$(cat "${LOCAL_SIGNING_KEY_PASSWORD_FILE}")"
  echo "[tauri:build] Using local updater signing password from ${LOCAL_SIGNING_KEY_PASSWORD_FILE}"
fi

if [[ -z "${TAURI_SIGNING_PRIVATE_KEY_PASSWORD:-}" ]]; then
  unset TAURI_SIGNING_PRIVATE_KEY_PASSWORD
fi

tauri_cmd=("${UI_DIR}/node_modules/.bin/tauri" "build")
if [[ -n "${TAURI_SIGNING_PRIVATE_KEY:-}" ]]; then
  tauri_cmd+=("-c" '{"bundle":{"createUpdaterArtifacts":true}}')
else
  echo "[tauri:build] No updater signing key detected; building without OTA artifacts."
fi
tauri_cmd+=("${build_args[@]}")

(
  cd "${UI_DIR}"
  "${tauri_cmd[@]}"
)

if [[ -z "${TAURI_SIGNING_PRIVATE_KEY:-}" ]]; then
  exit 0
fi

if [[ -n "${target_triple}" ]]; then
  bundle_root="${UI_DIR}/src-tauri/target/${target_triple}/release/bundle"
else
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
  echo "[tauri:build] Bundle root not found after build: ${bundle_root}" >&2
  exit 1
fi

updater_archive="$(find "${bundle_root}" -type f -name '*.app.tar.gz' | head -n 1)"
updater_signature="$(find "${bundle_root}" -type f -name '*.app.tar.gz.sig' | head -n 1)"

if [[ -z "${updater_archive}" || -z "${updater_signature}" ]]; then
  echo "[tauri:build] Signed updater artifacts were not generated under ${bundle_root}" >&2
  exit 1
fi

version="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' \
    "${UI_DIR}/src-tauri/tauri.conf.json"
)"
platform_key="${BRANDMINT_UPDATE_PLATFORM:-${BRANDMINT_UPDATER_PLATFORM:-darwin-aarch64}}"
base_url_root="${BRANDMINT_UPDATE_PRIMARY_BASE_URL:-${BRANDMINT_UPDATE_BASE_URL:-${DEFAULT_UPDATE_FALLBACK_BASE_URL}}}"
channel="${BRANDMINT_UPDATE_CHANNEL}"
base_url="${base_url_root%/}/${channel}"
manifest_path="${bundle_root}/latest.json"

python3 "${SCRIPT_DIR}/generate_updater_manifest.py" \
  --archive "${updater_archive}" \
  --signature "${updater_signature}" \
  --version "${version}" \
  --base-url "${base_url}" \
  --output "${manifest_path}" \
  --platform "${platform_key}"

echo "[tauri:build] Generated updater archive: ${updater_archive}"
echo "[tauri:build] Generated updater signature: ${updater_signature}"
echo "[tauri:build] Generated updater manifest: ${manifest_path}"
echo "[tauri:build] Updater channel: ${channel}"
echo "[tauri:build] Updater base URL: ${base_url}"
