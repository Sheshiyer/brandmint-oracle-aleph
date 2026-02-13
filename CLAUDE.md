# Brandmint — Agent Execution Guide

## The Golden Rule

**NEVER execute brandmint skills individually.** Always use the `bm launch` pipeline.

Brandmint is an orchestrated pipeline of 44 skills across 6 waves. Each skill depends on
outputs from prior skills. Running skills individually breaks the dependency chain and
produces incomplete or inconsistent results.

## How to Run the Pipeline

### Non-interactive (agent environments)

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario <scenario-id> \
  --waves 1-6 \
  --non-interactive
```

### With cost guard

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario brand-genesis \
  --waves 1-6 \
  --non-interactive \
  --max-cost 5.00
```

### Resume from a specific wave

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario brand-genesis \
  --resume-from 4 \
  --non-interactive
```

## How the Pipeline Works

1. `bm launch` computes a wave plan based on brand-config.yaml
2. For each skill, the executor writes a prompt to `.brandmint/prompts/{skill-id}.md`
3. The agent (you) executes the prompt and saves JSON output to `.brandmint/outputs/{skill-id}.json`
4. The executor polls for the output file and proceeds to the next skill
5. Visual asset skills (Wave 5-6) call FAL API directly — no agent intervention needed

## Post-Pipeline Publishing

After all waves complete, two publishing skills transform outputs into a documentation site:

### 1. Wiki Documentation Generation

Use the `wiki-doc-generator` skill to transform `.brandmint/outputs/*.json` into structured
markdown wiki pages. This skill uses 4-6 parallel agents via the Task tool.

### 2. Astro Wiki Site Build

Use the `markdown-to-astro-wiki` skill to convert wiki markdown into a glassmorphism Astro site.
Run `process-markdown.sh` with `--images <generated-dir>` to include visual assets.

## What NOT To Do

- Do NOT read individual SKILL.md files and execute them outside the pipeline
- Do NOT use `Confirm.ask()` or any interactive prompts when `--non-interactive` is set
- Do NOT skip skills on EOFError — use polling mode instead
- Do NOT generate visual assets manually — the pipeline handles FAL API calls

## Key Paths

- Brand config: `<brand-dir>/brand-config.yaml`
- Prompts: `<brand-dir>/.brandmint/prompts/`
- Outputs: `<brand-dir>/.brandmint/outputs/`
- Visual assets: `<brand-dir>/<brand-slug>/generated/`
- Pipeline state: `<brand-dir>/.brandmint/state.json`
