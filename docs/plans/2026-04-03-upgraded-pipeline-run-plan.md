# Upgraded Brandmint Pipeline Run Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Take the user-provided source artifact, turn it into a launchable approved Brandmint config, and run the current upgraded Brandmint pipeline with verified evidence.

**Architecture:** Follow the repo's pipeline-first contract: identify the intake source, validate environment and approval gating, create or confirm a launchable `brand-config.yaml`, then execute the supported `bm launch` path and record outputs. Do not run individual Brandmint skills manually; use the orchestrated CLI and approval contract already implemented in the repo.

**Tech Stack:** Python CLI (`bm` / `brandmint`), YAML config approval metadata, Brandmint wave executor, optional publishing pipeline, local shell verification.

---

### Task 1: Resolve The Input Artifact

**Files:**
- Modify: `tasks/todo.md`
- Reference: `CLAUDE.md`
- Reference: `SKILL.md`

**Step 1: Identify the exact source path**

Run:

```bash
pwd
rg --files -g 'brand-config.yaml' -g 'product.md' -g '*.md' .
```

Expected:
- Either an explicit intake file/folder is identified, or the task remains blocked pending the user-supplied path.

**Step 2: Record the resolved input**

Update:
- `tasks/todo.md`

Expected:
- The active task entry names the exact file/folder being processed.

### Task 2: Validate Environment And Launch Contract

**Files:**
- Reference: `brandmint/cli/launch.py`
- Reference: `brandmint/config_approval.py`
- Reference: `CLAUDE.md`

**Step 1: Check Brandmint entrypoints and prerequisites**

Run:

```bash
bm --help
python3 -c 'import yaml, rich'
```

Expected:
- CLI is runnable and Python dependencies needed for planning/launch are importable.

**Step 2: Confirm approval requirements**

Run:

```bash
sed -n '1,220p' brandmint/config_approval.py
sed -n '1,220p' brandmint/cli/launch.py
```

Expected:
- Launch requires an approved `brand-config.yaml` with no pending review fields.

### Task 3: Prepare A Launchable Brand Config

**Files:**
- Modify: `<user-input-brand-dir>/brand-config.yaml`
- Reference: `assets/brand-config-schema.yaml`
- Reference: `assets/example-tryambakam-noesis.yaml`

**Step 1: Create or inspect the config**

Run:

```bash
bm init --output <brand-dir>/brand-config.yaml
```

or inspect an existing config:

```bash
sed -n '1,240p' <brand-dir>/brand-config.yaml
```

Expected:
- A valid Brandmint config exists for the target artifact.

**Step 2: Ensure approval metadata is present and launchable**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from brandmint.config_approval import read_config_document, config_launch_status
path = Path("<brand-dir>/brand-config.yaml")
cfg = read_config_document(path)
print(config_launch_status(cfg))
PY
```

Expected:
- `is_launchable: True` before `bm launch` is attempted.

### Task 4: Execute The Upgraded Pipeline

**Files:**
- Modify: `<brand-dir>/.brandmint/state.json`
- Output: `<brand-dir>/.brandmint/outputs/*`
- Output: `<brand-dir>/<brand-slug>/generated/*`

**Step 1: Choose scenario and waves**

Run:

```bash
bm plan recommend --config <brand-dir>/brand-config.yaml
```

Expected:
- A scenario recommendation is available, or a repo-supported default is chosen explicitly.

**Step 2: Run the pipeline**

Run:

```bash
bm launch --config <brand-dir>/brand-config.yaml \
  --scenario <scenario-id> \
  --waves <wave-range> \
  --non-interactive
```

Expected:
- The pipeline starts cleanly and produces `.brandmint` state/output artifacts without approval errors.

### Task 5: Verify Outputs Before Claiming Success

**Files:**
- Modify: `tasks/todo.md`
- Reference: `<brand-dir>/.brandmint/state.json`
- Reference: `<brand-dir>/.brandmint/outputs/`

**Step 1: Inspect state and outputs**

Run:

```bash
find <brand-dir>/.brandmint -maxdepth 2 -type f | sort
bm report --config <brand-dir>/brand-config.yaml
```

Expected:
- Fresh evidence shows what completed, what failed, and what artifacts were produced.

**Step 2: Document review**

Update:
- `tasks/todo.md`

Expected:
- The review section records commands run, exit status, generated outputs, and any blockers or follow-up actions.
