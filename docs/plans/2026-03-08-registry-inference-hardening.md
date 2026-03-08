# Registry Inference Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the registry/import hardening cluster that closes issues `#60`, `#62`, and `#63` without mixing in unrelated provider, UI, or Tauri work.

**Architecture:** Rework the skill registry so CLI and runtime share one discovery contract with explicit conflict handling, then add a dedicated importer/validator path for normalized `inference-sh/skills`. Keep the PR self-contained: registry core, CLI surface, import scripts, normalized pack, tests, and pack-integrity CI only.

**Tech Stack:** Python, Typer CLI, pytest, GitHub Actions, YAML frontmatter parsing.

---

### Task 1: Port registry core hardening

**Files:**
- Modify: `brandmint/core/skills_registry.py`

**Steps:**
1. Port the local conflict-policy implementation into the worktree.
2. Port alias resolution and unified skill ID normalization.
3. Port recursive discovery with `SKILL.md`, `skill.md`, and guarded `instructions.md` handling.
4. Preserve orchestrator/local/Claude merge behavior while surfacing conflicts instead of silent overwrite.
5. Verify the file imports cleanly.

**Run:**
- `python3 -m py_compile brandmint/core/skills_registry.py`

### Task 2: Port registry CLI parity and diagnostics

**Files:**
- Modify: `brandmint/cli/registry.py`

**Steps:**
1. Switch CLI listing/info to use `SkillsRegistry` directly.
2. Add registry sync output path support.
3. Add `run_doctor(strict=False)` diagnostics for inventory/conflicts/wave resolvability.
4. Keep existing visual asset listing behavior intact.

**Run:**
- `python3 -m py_compile brandmint/cli/registry.py`

### Task 3: Add normalized import and validation tooling

**Files:**
- Create: `scripts/import_inference_skills.py`
- Create: `scripts/validate_skill_pack.py`
- Create: `.github/workflows/inference-pack-integrity.yml`

**Steps:**
1. Add importer for pinned upstream snapshot + normalized `infsh-*` pack generation.
2. Add validator for frontmatter, required fields, duplicate IDs, and skill refs.
3. Add CI workflow that runs the validator on PRs and pushes.

**Run:**
- `python3 scripts/validate_skill_pack.py --pack-root skills/external/inference-sh/normalized`

### Task 4: Add normalized pack and regression tests

**Files:**
- Create: `skills/external/inference-sh/normalized/allowlist.yaml`
- Create: `skills/external/inference-sh/normalized/import-manifest.json`
- Create: `skills/external/inference-sh/normalized/*/SKILL.md`
- Create: `tests/test_skills_registry.py`

**Steps:**
1. Add the normalized allowlist and manifest.
2. Add the imported normalized skill set used by the inference integration path.
3. Add pytest coverage for alias resolution, conflict policy, recursion, and guarded `instructions.md`.

**Run:**
- `pytest -q tests/test_skills_registry.py`

### Task 5: Verify the cluster and prepare the PR branch

**Files:**
- Review: `brandmint/core/skills_registry.py`
- Review: `brandmint/cli/registry.py`
- Review: `scripts/import_inference_skills.py`
- Review: `scripts/validate_skill_pack.py`
- Review: `.github/workflows/inference-pack-integrity.yml`
- Review: `tests/test_skills_registry.py`

**Steps:**
1. Run scoped verification commands.
2. Confirm the branch contains only `#60/#62/#63` files.
3. Summarize issue closure readiness and any residual risks.
4. Commit on `codex/registry-inference-hardening`.

**Run:**
- `python3 -m py_compile brandmint/core/skills_registry.py brandmint/cli/registry.py scripts/import_inference_skills.py scripts/validate_skill_pack.py`
- `pytest -q tests/test_skills_registry.py`
- `python3 -m brandmint.cli.app registry doctor --strict`

