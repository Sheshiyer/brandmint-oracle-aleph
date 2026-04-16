# Release Checklist

## Pre-release
- [ ] `pyproject.toml` version updated
- [ ] Release notes updated (`.github/RELEASE_NOTES.md`)
- [ ] Version-specific GitHub release body prepared (`.github/RELEASE_v{VERSION}.md`)
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
  - bootstrap trust-rotation release: publish manual-install assets first, keep OTA payload on `bootstrap`, and call out the one-time reinstall requirement in the GitHub release notes
- [ ] `publish-tauri-macos.yml` workflow triggered and succeeded
- [ ] GitHub Release includes `Brandmint_{VERSION}_macos-aarch64.dmg`
- [ ] GitHub Release includes `Brandmint_{VERSION}_macos-aarch64.app.zip`
- [ ] If doing a bootstrap trust-rotation release, GitHub Release notes explicitly say existing installs must reinstall manually once
- [ ] Artifact names contain correct version
- [ ] OTA bootstrap manifest returns `200` at `https://brandmintupdates.thoughtseed.space/bootstrap/latest.json` when using bootstrap mode
- [ ] OTA bootstrap archive returns `200` at `https://brandmintupdates.thoughtseed.space/bootstrap/Brandmint.app.tar.gz` when using bootstrap mode
- [ ] If public macOS distribution is required, notarize/staple the signed release assets before broad rollout

## Post-release verification
- [ ] `brew tap Sheshiyer/brandmint`
- [ ] `brew install brandmint`
- [ ] `bm --help`
- [ ] Download DMG from GitHub Release and verify it mounts
- [ ] Download .app.zip and verify app launches
- [ ] If this was a bootstrap trust-rotation release, install `v{VERSION}` manually once and confirm later OTA checks use the new updater line
