# Release Checklist

## Pre-release
- [ ] `pyproject.toml` version updated
- [ ] Release notes updated (`.github/RELEASE_NOTES.md`)
- [ ] Changelog updated (`CHANGELOG.md`)

## Homebrew
- [ ] Tap formula updated to new tag + sha256
- [ ] `brew install --build-from-source brandmint`
- [ ] `brew test brandmint`
- [ ] `brew audit --strict --online brandmint`

## Package publishing
- [ ] GHCR workflow success
- [ ] GitHub release published with correct notes

## Tauri Desktop App
- [ ] Choose release mode:
  - unsigned internal build: no Apple secrets, artifacts publish for internal/right-click-open use
  - signed distribution build: configure `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_PASSWORD`, and `APPLE_TEAM_ID`
- [ ] `publish-tauri-macos.yml` workflow triggered and succeeded
- [ ] GitHub Release includes `Brandmint_{VERSION}_macos-aarch64.dmg`
- [ ] GitHub Release includes `Brandmint_{VERSION}_macos-aarch64.app.zip`
- [ ] Artifact names contain correct version
- [ ] If public macOS distribution is required, notarize/staple the signed release assets before broad rollout

## Post-release verification
- [ ] `brew tap Sheshiyer/brandmint`
- [ ] `brew install brandmint`
- [ ] `bm --help`
- [ ] Download DMG from GitHub Release and verify it mounts
- [ ] Download .app.zip and verify app launches
