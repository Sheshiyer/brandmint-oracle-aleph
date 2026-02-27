# Homebrew Packaging Decision Record

## Scope
This repository (`Sheshiyer/brandmint-oracle-aleph`) is the source of truth for Brandmint releases.
Homebrew distribution is delivered via a tap repository:

- `Sheshiyer/homebrew-brandmint`

## Install target
```bash
brew tap Sheshiyer/brandmint
brew install brandmint
bm --help
```

## Packaging strategy
- **Formula source:** GitHub release tarball from this repository
- **Python target:** `python@3.11`
- **Binaries:** `brandmint` and `bm` (formula symlink)
- **Version policy:** semver tags in `vX.Y.Z` format

## Formula maintenance
- Formula path in tap: `Formula/brandmint.rb`
- On each release:
  1. Update formula `url` to new tag tarball
  2. Update formula `sha256`
  3. Run `brew install --build-from-source`, `brew test`, `brew audit --strict --online`

## Automation model
Current repo provides a release workflow that can update the tap formula using a PAT secret (`HOMEBREW_TAP_TOKEN`).

## Known constraints
- Homebrew core inclusion is out-of-scope for v1
- Tap-first distribution is supported and documented
