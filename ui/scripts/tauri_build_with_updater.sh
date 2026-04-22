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
bundles_arg_provided=0
for ((i = 0; i < ${#build_args[@]}; i += 1)); do
  if [[ "${build_args[$i]}" == "--target" ]] && (( i + 1 < ${#build_args[@]} )); then
    target_triple="${build_args[$((i + 1))]}"
  elif [[ "${build_args[$i]}" == "--bundles" ]] && (( i + 1 < ${#build_args[@]} )); then
    bundles_arg_provided=1
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

resolve_bundle_root() {
  if [[ -n "${target_triple}" ]]; then
    echo "${UI_DIR}/src-tauri/target/${target_triple}/release/bundle"
    return 0
  fi

  local inferred_root="${UI_DIR}/src-tauri/target/release/bundle"
  if [[ -d "${inferred_root}" ]]; then
    echo "${inferred_root}"
    return 0
  fi

  case "$(uname -m)" in
    arm64|aarch64)
      inferred_root="${UI_DIR}/src-tauri/target/aarch64-apple-darwin/release/bundle"
      ;;
    x86_64)
      inferred_root="${UI_DIR}/src-tauri/target/x86_64-apple-darwin/release/bundle"
      ;;
    *)
      ;;
  esac

  echo "${inferred_root}"
}

find_macos_app_bundle() {
  local bundle_root="$1"
  local default_app="${bundle_root}/macos/Brandmint.app"

  if [[ -d "${default_app}" ]]; then
    echo "${default_app}"
    return 0
  fi

  find "${bundle_root}" -maxdepth 2 -type d -name '*.app' | head -n 1
}

verify_macos_bundle_signature() {
  local app_bundle="$1"
  codesign --verify --deep --strict --verbose=2 "${app_bundle}"
}

create_manual_macos_dmg() {
  local bundle_root="$1"
  local app_bundle="$2"
  local version dmg_path staging_dir staging_app_dir

  if [[ "$(uname -s)" != "Darwin" || -z "${app_bundle}" || ! -d "${app_bundle}" ]]; then
    return 0
  fi

  version="$(
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' \
      "${UI_DIR}/src-tauri/tauri.conf.json"
  )"
  dmg_path="${bundle_root}/Brandmint_${version}_macos-aarch64.dmg"
  staging_dir="$(mktemp -d "${TMPDIR:-/tmp}/brandmint-dmg.XXXXXX")"
  staging_app_dir="${staging_dir}/Brandmint"

  rm -f "${dmg_path}"
  mkdir -p "${staging_app_dir}"
  ditto "${app_bundle}" "${staging_app_dir}/Brandmint.app"
  ln -s /Applications "${staging_app_dir}/Applications"

  hdiutil create -ov \
    -volname "Brandmint" \
    -srcfolder "${staging_app_dir}" \
    -fs HFS+ \
    -format UDZO \
    "${dmg_path}"

  rm -rf "${staging_dir}"

  echo "[tauri:build] Created manual DMG: ${dmg_path}"
}

ensure_macos_bundle_signature() {
  local app_bundle="$1"

  if [[ "$(uname -s)" != "Darwin" || -z "${app_bundle}" || ! -d "${app_bundle}" ]]; then
    return 0
  fi

  if verify_macos_bundle_signature "${app_bundle}" >/dev/null 2>&1; then
    echo "[tauri:build] Verified macOS bundle signature: ${app_bundle}"
    return 0
  fi

  if [[ -n "${APPLE_SIGNING_IDENTITY:-}" ]]; then
    echo "[tauri:build] macOS bundle failed signature verification after signed build: ${app_bundle}" >&2
    verify_macos_bundle_signature "${app_bundle}"
    exit 1
  fi

  echo "[tauri:build] macOS bundle signature is incomplete; applying ad-hoc bundle signature to avoid shipping a broken app bundle."
  codesign --force --deep --sign - "${app_bundle}"
  verify_macos_bundle_signature "${app_bundle}"
}

prepare_local_bridge_runtime_hint() {
  local app_bundle="$1"
  local resources_dir repo_root hint_path

  if [[ "$(uname -s)" != "Darwin" || -z "${app_bundle}" || ! -d "${app_bundle}" ]]; then
    return 0
  fi

  if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]]; then
    return 0
  fi

  repo_root="$(cd "${UI_DIR}/.." && pwd)"
  resources_dir="${app_bundle}/Contents/Resources"
  hint_path="${resources_dir}/brandmint-root.txt"

  mkdir -p "${resources_dir}"
  printf '%s\n' "${repo_root}" > "${hint_path}"
  echo "[tauri:build] Wrote local repo root hint for bundled bridge: ${hint_path}"
}

regenerate_updater_artifacts() {
  local app_bundle="$1"
  local app_parent archive_path signature_path

  if [[ -z "${TAURI_SIGNING_PRIVATE_KEY:-}" || -z "${app_bundle}" || ! -d "${app_bundle}" ]]; then
    return 0
  fi

  app_parent="$(dirname "${app_bundle}")"
  archive_path="${app_parent}/$(basename "${app_bundle}").tar.gz"
  signature_path="${archive_path}.sig"

  rm -f "${archive_path}" "${signature_path}"
  (
    cd "${app_parent}"
    COPYFILE_DISABLE=1 tar -czf "$(basename "${archive_path}")" "$(basename "${app_bundle}")"
  )

  "${UI_DIR}/node_modules/.bin/tauri" signer sign "${archive_path}"

  if [[ ! -f "${signature_path}" ]]; then
    echo "[tauri:build] Updater signature was not generated for ${archive_path}" >&2
    exit 1
  fi

  echo "[tauri:build] Regenerated updater archive: ${archive_path}"
  echo "[tauri:build] Regenerated updater signature: ${signature_path}"
}

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
manual_macos_dmg=0
if [[ "$(uname -s)" == "Darwin" && -z "${CI:-}" && -z "${GITHUB_ACTIONS:-}" && "${bundles_arg_provided}" -eq 0 ]]; then
  build_args+=("--bundles" "app")
  manual_macos_dmg=1
  echo "[tauri:build] Local macOS build detected; forcing app-only Tauri bundle and generating DMG manually."
fi
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

bundle_root="$(resolve_bundle_root)"

if [[ ! -d "${bundle_root}" ]]; then
  echo "[tauri:build] Bundle root not found after build: ${bundle_root}" >&2
  exit 1
fi

app_bundle="$(find_macos_app_bundle "${bundle_root}")"
prepare_local_bridge_runtime_hint "${app_bundle}"
ensure_macos_bundle_signature "${app_bundle}"
if [[ "${manual_macos_dmg}" -eq 1 ]]; then
  create_manual_macos_dmg "${bundle_root}" "${app_bundle}"
fi

if [[ -z "${TAURI_SIGNING_PRIVATE_KEY:-}" ]]; then
  exit 0
fi

regenerate_updater_artifacts "${app_bundle}"

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
