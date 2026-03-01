#!/usr/bin/env bash
# twitter_sync_all.sh — Unified wrapper for Brandmint Twitter sync pipeline.
#
# Runs twitter_sync.py (discover + curate) then download_tweet_assets.py
# (download images + write prompt files) in sequence.
#
# Usage:
#   ./scripts/twitter_sync_all.sh              # full sync
#   ./scripts/twitter_sync_all.sh --dry-run    # preview only
#   ./scripts/twitter_sync_all.sh --skip-download  # sync only, no assets
#   ./scripts/twitter_sync_all.sh --min-likes=5    # override likes threshold
#
# Environment:
#   BRANDMINT_SYNC_LOG_DIR  — override log directory (default: references/twitter-sync/logs)
#   BRANDMINT_MIN_LIKES     — override min likes (passed to both scripts)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON3="$(command -v python3)"
BIRD_CLI="/opt/homebrew/bin/bird"
LOG_DIR="${BRANDMINT_SYNC_LOG_DIR:-${ROOT_DIR}/references/twitter-sync/logs}"
DATE_STR="$(date +%Y-%m-%d)"
LOG_FILE="${LOG_DIR}/sync-${DATE_STR}.log"

# Parse arguments
DRY_RUN=""
SKIP_DOWNLOAD=""
EXTRA_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --dry-run)       DRY_RUN="--dry-run" ;;
    --skip-download) SKIP_DOWNLOAD="1" ;;
    --min-likes=*)   EXTRA_ARGS+=("--min-likes" "${arg#*=}") ;;
    *)               EXTRA_ARGS+=("$arg") ;;
  esac
done

# Add env-based min-likes if set and not overridden via CLI
if [[ -n "${BRANDMINT_MIN_LIKES:-}" ]]; then
  has_min_likes=false
  for a in "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"; do
    if [[ "$a" == "--min-likes" ]]; then has_min_likes=true; fi
  done
  if [[ "$has_min_likes" == "false" ]]; then
    EXTRA_ARGS+=("--min-likes" "${BRANDMINT_MIN_LIKES}")
  fi
fi

# Preflight checks
echo "BRANDMINT — Twitter Sync Pipeline"
echo "=================================="
echo "  Date:     ${DATE_STR}"
echo "  Root:     ${ROOT_DIR}"
echo "  Dry run:  ${DRY_RUN:-no}"
echo "  Download: ${SKIP_DOWNLOAD:+skipped}${SKIP_DOWNLOAD:-yes}"
echo ""

if [[ ! -x "${BIRD_CLI}" ]]; then
  echo "ERROR: bird CLI not found at ${BIRD_CLI}" >&2
  exit 1
fi

if ! "${BIRD_CLI}" whoami 2>&1 | grep -q "^🙋"; then
  echo "ERROR: bird CLI not authenticated. Run 'bird auth' first." >&2
  exit 1
fi

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Step 1: Twitter Discovery + Curate
echo "── Step 1: Twitter Sync (discover + curate) ──"
"${PYTHON3}" "${ROOT_DIR}/scripts/twitter_sync.py" \
  ${DRY_RUN} \
  "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}" \
  2>&1 | tee -a "${LOG_FILE}"

SYNC_EXIT=${PIPESTATUS[0]}
if [[ ${SYNC_EXIT} -ne 0 ]]; then
  echo "ERROR: twitter_sync.py exited with code ${SYNC_EXIT}" >&2
  exit ${SYNC_EXIT}
fi

# Step 2: Download assets (unless skipped or dry run)
if [[ -z "${SKIP_DOWNLOAD}" ]] && [[ -z "${DRY_RUN}" ]]; then
  echo ""
  echo "── Step 2: Download Tweet Assets ──"
  "${PYTHON3}" "${ROOT_DIR}/scripts/download_tweet_assets.py" \
    "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}" \
    2>&1 | tee -a "${LOG_FILE}"

  DL_EXIT=${PIPESTATUS[0]}
  if [[ ${DL_EXIT} -ne 0 ]]; then
    echo "ERROR: download_tweet_assets.py exited with code ${DL_EXIT}" >&2
    exit ${DL_EXIT}
  fi
elif [[ -n "${DRY_RUN}" ]] && [[ -z "${SKIP_DOWNLOAD}" ]]; then
  echo ""
  echo "── Step 2: Download Tweet Assets (dry run) ──"
  "${PYTHON3}" "${ROOT_DIR}/scripts/download_tweet_assets.py" \
    --dry-run \
    "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}" \
    2>&1 | tee -a "${LOG_FILE}"
fi

# Summary
echo ""
echo "=================================="
echo "  Sync pipeline complete: ${DATE_STR}"
echo "  Log: ${LOG_FILE}"
echo "=================================="
