Scan the brandmint repository for changes since the last git tag and update all documentation files to reflect new features.

## Steps

1. Run the change scanner:
   ```bash
   .venv/bin/python scripts/update-release-docs.py --summary
   ```

2. Review the change summary to understand what's new.

3. If a version bump is needed, run:
   ```bash
   .venv/bin/python scripts/update-release-docs.py --version <NEW_VERSION>
   ```
   This updates version strings across all doc files automatically.

4. For areas flagged as needing manual review, surgically update these files:
   - `README.md` — Architecture diagram, wave table, feature sections, CLI reference
   - `CLAUDE.md` — Pipeline steps, wave 7 section, key paths
   - `SKILL.md` — Skill categories, wave table, publishing pipeline, key files, project structure
   - `.github/RELEASE_NOTES.md` — Add new version section at top
   - `docs/product-description.md` — Features list, specs JSON
   - `.github/copilot-instructions.md` — Wave table, publishing section, project structure
   - `.cursorrules` — Wave execution, CLI commands, project structure

5. Rules for updating:
   - SURGICAL edits only — add/modify specific sections, never rewrite entire files
   - Preserve existing formatting and section structure
   - Add new wave/feature rows to existing tables (don't rebuild tables)
   - Update counts (skill count, wave count) where referenced
   - Update version badges and version strings consistently
   - Add new key paths where deliverable directories are listed

6. After updates, verify with:
   ```bash
   git diff --stat  # Check no unexpected deletions
   ```
