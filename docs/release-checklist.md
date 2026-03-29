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

## Desktop release assets
- [ ] `publish-tauri-release-assets.yml` workflow success
- [ ] GitHub Release includes the generated macOS `.dmg`
- [ ] GitHub Release includes the archived macOS `.app.zip`
- [ ] Uploaded asset names reflect the release version and runner architecture
- [ ] Confirm current limitation is acceptable: assets are unsigned and not notarized unless signing/notarization is configured separately

## Post-release verification
- [ ] `brew tap Sheshiyer/brandmint`
- [ ] `brew install brandmint`
- [ ] `bm --help`
- [ ] Download the macOS `.dmg` from GitHub Releases and confirm it mounts
- [ ] Download the macOS `.app.zip`, unzip it, and confirm `Brandmint.app` opens on a test Mac
