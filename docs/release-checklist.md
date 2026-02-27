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

## Post-release verification
- [ ] `brew tap Sheshiyer/brandmint`
- [ ] `brew install brandmint`
- [ ] `bm --help`
