# Brandmint Development Makefile
# ─────────────────────────────

SHELL := /bin/bash
export PATH := $(HOME)/.cargo/bin:/opt/homebrew/bin:$(PATH)

UI_DIR := ui
TAURI_DIR := $(UI_DIR)/src-tauri

.PHONY: dev build clean sidecar install bundle-sidecar-venv

## dev — Start Tauri dev mode (Vite hot-reload + Rust backend + sidecar)
dev:
	cd $(UI_DIR) && npm run tauri:dev

## build — Production build (creates .app and .dmg)
build:
	cd $(UI_DIR) && npm run tauri:build

## clean — Remove build artifacts
clean:
	cd $(TAURI_DIR) && cargo clean
	rm -rf $(UI_DIR)/dist

## sidecar — Test the sidecar bridge standalone
sidecar:
	python3 scripts/ui_backend_bridge.py

## install — Install frontend + Rust dependencies
install:
	cd $(UI_DIR) && npm install
	cd $(TAURI_DIR) && cargo build

## bundle-sidecar-venv — Prepare a portable Python env beside the Tauri sidecar wrapper
bundle-sidecar-venv:
	python3 -m venv $(TAURI_DIR)/binaries/venv
	$(TAURI_DIR)/binaries/venv/bin/pip install --upgrade pip
	$(TAURI_DIR)/binaries/venv/bin/pip install .

## check — Lint and type-check
check:
	cd $(TAURI_DIR) && cargo clippy
	cd $(UI_DIR) && npx tsc --noEmit

## help — Show available targets
help:
	@grep -E '^## ' Makefile | sed 's/^## /  /'
