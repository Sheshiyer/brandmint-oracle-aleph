# Brandmint v4.4.1

`v4.4.1` is a bootstrap desktop release for Brandmint.

This cut rotates the desktop updater trust root. If you already have an older Brandmint desktop build installed, update by downloading the DMG or `.app.zip` from this release and reinstalling manually one time. After that bootstrap reinstall, future OTA updates can continue on the new Brandmint signing key.

## Included Release Assets

- `Brandmint_4.4.1_macos-aarch64.dmg`
- `Brandmint_4.4.1_macos-aarch64.app.zip`
- `Brandmint.app.tar.gz`
- `Brandmint.app.tar.gz.sig`
- `latest.json`

## Highlights

- Provider fallback chain in the visual execution backend via `generation.fallback_order`
- Safe state validation and auto-repair for execution + NotebookLM state files
- Brandmint-specific signed Tauri updater trust root
- OTA payload staged on `brandmintupdates.thoughtseed.space`

## Install / Update

1. Quit any older Brandmint desktop app you have installed.
2. Download `Brandmint_4.4.1_macos-aarch64.dmg` and install Brandmint, or use `Brandmint_4.4.1_macos-aarch64.app.zip` if you need the unpacked app bundle path.
3. Launch `v4.4.1` once to move onto the new updater trust root.
4. Future OTA releases can then continue from the new Brandmint signing line.

## OTA Notes

- Bootstrap manifest: `https://brandmintupdates.thoughtseed.space/bootstrap/latest.json`
- Bootstrap archive: `https://brandmintupdates.thoughtseed.space/bootstrap/Brandmint.app.tar.gz`
- `stable` was intentionally left untouched during this prep so the bootstrap line could be staged safely first.
