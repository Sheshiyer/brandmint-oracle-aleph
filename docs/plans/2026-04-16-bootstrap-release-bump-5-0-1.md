# Bootstrap Release Bump to v5.0.1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the mistaken `v4.4.1` bootstrap desktop release with `v5.0.1`, rebuild the signed assets, and publish the corrected GitHub release.

**Architecture:** Keep the already-landed updater/bootstrap code path intact and only retarget the versioned release surfaces. Build a fresh signed artifact set for `v5.0.1`, publish a new GitHub release from the corrected commit, then retire the accidental `v4.4.1` prerelease so the release inventory converges on the intended bootstrap cut.

**Tech Stack:** Git, GitHub CLI, Tauri v2, npm/Vite, Cargo, local Brandmint signing key, Cloudflare-hosted updater artifacts

---

### Task 1: Audit versioned release surfaces

**Files:**
- Modify: `tasks/todo.md`
- Inspect: release docs, Tauri config, GitHub release notes/templates, build outputs

**Step 1: Enumerate repo references**

Run:

```bash
rg -n "4\\.4\\.1|RELEASE_v4\\.4\\.1|Brandmint_4\\.4\\.1" .
```

Expected: exact list of files and release assets that still point at the old bootstrap version.

**Step 2: Enumerate GitHub release state**

Run:

```bash
gh release list --repo Sheshiyer/brandmint-oracle-aleph --limit 8
```

Expected: `v4.4.1` prerelease plus the existing `v5.1.0` latest release.

### Task 2: Update repo release surfaces to v5.0.1

**Files:**
- Modify: `.github/RELEASE_NOTES.md`
- Create: `.github/RELEASE_v5.0.1.md`
- Delete/replace usage of: `.github/RELEASE_v4.4.1.md`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `docs/release-checklist.md`
- Modify: `ui/package.json`
- Modify: `ui/src-tauri/Cargo.toml`
- Modify: `ui/src-tauri/Cargo.lock`
- Modify: `ui/src-tauri/tauri.conf.json`

**Step 1: Replace version references**

Update all release-facing text and desktop version surfaces from `4.4.1` to `5.0.1`.

**Step 2: Align release asset names**

Ensure notes and README reference:

```text
Brandmint_5.0.1_macos-aarch64.dmg
Brandmint_5.0.1_macos-aarch64.app.zip
Brandmint.app.tar.gz
Brandmint.app.tar.gz.sig
latest.json
```

**Step 3: Verify diff scope**

Run:

```bash
git diff --stat
```

Expected: only the intended release/version files change at this step.

### Task 3: Rebuild and verify signed assets

**Files:**
- Rebuild outputs under: `ui/src-tauri/target/aarch64-apple-darwin/release/bundle/`

**Step 1: Run frontend build**

Run:

```bash
npm --prefix ui run build
```

Expected: production frontend build passes.

**Step 2: Run Tauri signed build**

Run:

```bash
npm --prefix ui run tauri:build -- --bundles app --target aarch64-apple-darwin
```

Expected: fresh `v5.0.1` DMG, `.app.zip`, updater archive, signature, and `latest.json`.

**Step 3: Verify artifact names**

Run:

```bash
ls -l ui/src-tauri/target/aarch64-apple-darwin/release/bundle/Brandmint_5.0.1_macos-aarch64.dmg \
      ui/src-tauri/target/aarch64-apple-darwin/release/bundle/Brandmint_5.0.1_macos-aarch64.app.zip \
      ui/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/Brandmint.app.tar.gz \
      ui/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/Brandmint.app.tar.gz.sig \
      ui/src-tauri/target/aarch64-apple-darwin/release/bundle/latest.json
```

Expected: all files exist and carry fresh timestamps from the rebuild.

### Task 4: Publish corrected GitHub release

**Files:**
- Modify remote GitHub release/tag state for `v4.4.1`
- Create remote GitHub release/tag state for `v5.0.1`

**Step 1: Commit and push corrected source**

Run:

```bash
git add <release files>
git commit -m "release(desktop): bump bootstrap to 5.0.1"
git push origin main
```

Expected: corrected source lands on `origin/main`.

**Step 2: Create corrected release**

Run:

```bash
gh release create v5.0.1 <assets...> \
  --repo Sheshiyer/brandmint-oracle-aleph \
  --target <commit-sha> \
  --title "Brandmint v5.0.1 - Bootstrap Desktop Release" \
  --notes-file .github/RELEASE_v5.0.1.md \
  --latest
```

Expected: GitHub publishes the corrected bootstrap cut.

**Step 3: Retire mistaken prerelease**

Run:

```bash
gh release delete v4.4.1 --repo Sheshiyer/brandmint-oracle-aleph --yes
git push origin :refs/tags/v4.4.1
```

Expected: the accidental `v4.4.1` prerelease/tag is removed so the release inventory is not split across two bootstrap tags.

### Task 5: Final verification and documentation

**Files:**
- Modify: `tasks/todo.md`
- Modify: `tasks/lessons.md`

**Step 1: Verify final GitHub release state**

Run:

```bash
gh release list --repo Sheshiyer/brandmint-oracle-aleph --limit 8
gh release view v5.0.1 --repo Sheshiyer/brandmint-oracle-aleph
```

Expected: `v5.0.1` visible as the corrected bootstrap release with the expected assets.

**Step 2: Record review + lessons**

Document:
- exact commit SHA
- published release URL
- final asset list
- lesson about checking visible GitHub surfaces before declaring release success
