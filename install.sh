#!/bin/bash
# brandmint installer - curl-installable setup script
# Usage: curl -sSL https://raw.githubusercontent.com/brandmint/brandmint/main/install.sh | bash

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}▶${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*" >&2; }

# Detect installation target
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}"
INSTALL_DIR="${SKILLS_DIR}/brandmint"
REPO_URL="https://github.com/brandmint/brandmint.git"

info "Installing brandmint to: ${INSTALL_DIR}"

# Create skills directory if it doesn't exist
mkdir -p "${SKILLS_DIR}"

# Clone or update repository
if [ -d "${INSTALL_DIR}/.git" ]; then
    info "Updating existing installation..."
    cd "${INSTALL_DIR}"
    git pull --ff-only || {
        warn "Fast-forward update failed. You may have local changes."
        exit 1
    }
else
    info "Cloning brandmint repository..."
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
fi

# Install Python package with fallback strategy
info "Installing brandmint Python package..."

if command -v pipx >/dev/null 2>&1; then
    info "Using pipx (recommended)..."
    pipx install --force "${INSTALL_DIR}" && INSTALL_METHOD="pipx"
elif command -v uv >/dev/null 2>&1; then
    info "Using uv tool..."
    uv tool install "${INSTALL_DIR}" && INSTALL_METHOD="uv"
elif command -v pip >/dev/null 2>&1; then
    warn "Using pip --user (consider installing pipx for better isolation)..."
    pip install --user --force-reinstall "${INSTALL_DIR}" && INSTALL_METHOD="pip"
else
    error "No Python package manager found (pipx/uv/pip). Please install Python 3.8+."
    exit 1
fi

info "Installed via: ${INSTALL_METHOD}"

# Verify installation
info "Verifying installation..."
if command -v bm >/dev/null 2>&1; then
    VERSION=$(bm --version 2>/dev/null || echo "unknown")
    info "Running post-install check..."
    bm install check || warn "Post-install check reported issues (see above)"
    echo ""
    echo -e "${GREEN}✓ brandmint successfully installed!${NC}"
    echo -e "  Version: ${VERSION}"
    echo -e "  Location: ${INSTALL_DIR}"
    echo -e "  CLI: bm"
    echo ""
    echo "Get started with: bm --help"
else
    error "Installation completed but 'bm' command not found in PATH."
    error "You may need to add ~/.local/bin to your PATH."
    exit 1
fi
