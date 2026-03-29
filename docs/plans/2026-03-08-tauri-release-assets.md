# Tauri Release Assets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a release workflow that publishes macOS Tauri desktop artifacts (`.dmg` and zipped `.app`) to GitHub Releases for tagged Brandmint releases.

**Architecture:** Keep the change isolated to release automation and release docs. Reuse the existing Tauri bundle configuration in `ui/src-tauri/tauri.conf.json`, build on `macos-latest` when a GitHub Release is published, archive the generated app bundle with `ditto`, then upload the `.dmg` and `.app.zip` back to the same GitHub Release.

**Tech Stack:** GitHub Actions, Tauri v2 CLI, npm, Rust, macOS bundling tools (`ditto`), GitHub CLI.

---

### Task 1: Inspect existing release and Tauri bundle configuration

**Files:**
- Read: `.github/workflows/publish-ghcr.yml`
- Read: `.github/workflows/update-homebrew-tap.yml`
- Read: `ui/src-tauri/tauri.conf.json`
- Read: `docs/release-checklist.md`

**Step 1: Confirm current release triggers**

Run: `sed -n '1,220p' .github/workflows/publish-ghcr.yml .github/workflows/update-homebrew-tap.yml`
Expected: both workflows trigger on `release.published` and do not yet handle desktop assets.

**Step 2: Confirm Tauri bundle targets**

Run: `sed -n '1,220p' ui/src-tauri/tauri.conf.json`
Expected: `bundle.active=true` and `targets` include both `dmg` and `app`.

### Task 2: Add the desktop release workflow

**Files:**
- Create: `.github/workflows/publish-tauri-release-assets.yml`

**Step 1: Write the workflow**

Implement a job that:
- runs on `macos-latest`
- triggers on `release.published` and `workflow_dispatch`
- resolves the release tag
- installs Node 20 without npm cache coupling because `ui/` does not currently ship a committed lockfile
- installs Rust stable
- runs `npm install --no-package-lock` in `ui/`
- builds the app via `npm run tauri build -- --bundles app,dmg`
- archives `Brandmint.app` into a versioned `.app.zip`
- uploads the generated `.dmg` and `.app.zip` to the existing GitHub Release with overwrite safety

**Step 2: Verify workflow syntax**

Run: `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/publish-tauri-release-assets.yml")'`
Expected: no YAML parse errors.

### Task 3: Update release documentation

**Files:**
- Modify: `docs/release-checklist.md`

**Step 1: Add desktop release asset checks**

Document:
- the new workflow name
- expected downloadable assets (`.dmg`, `.app.zip`)
- post-release verification steps
- current limitations: unsigned, not notarized unless signing secrets/config are added later

**Step 2: Sanity-check doc references**

Run: `rg -n 'Desktop release assets|publish-tauri-release-assets|app.zip|dmg' docs/release-checklist.md`
Expected: new desktop release section is present.

### Task 4: Run scoped verification

**Files:**
- Read/verify: `.github/workflows/publish-tauri-release-assets.yml`
- Read/verify: `ui/src-tauri/tauri.conf.json`

**Step 1: Validate Tauri config JSON**

Run: `python3 -m json.tool ui/src-tauri/tauri.conf.json >/dev/null`
Expected: valid JSON.

**Step 2: Check local frontend build baseline**

Run: `npm --prefix ui install --no-package-lock && npm --prefix ui run build`
Expected: either pass, or fail with a pre-existing frontend build problem that must be called out as outside `#113` scope.

**Step 3: Record changed files and limitations**

Report exact file list, verification results, and any known release limitations such as missing code signing and notarization.
