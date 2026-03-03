# Brandmint — Agent Execution Guide

## The Golden Rule

**NEVER execute brandmint skills individually.** Always use the `bm launch` pipeline.

Brandmint is an orchestrated pipeline of 44 skills across 7 waves plus NotebookLM publishing. Each skill depends on
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
5. Visual asset skills (Wave 3-5) call FAL API directly — no agent intervention needed
6. Wave 7 (Publishing) runs NotebookLM: creates notebook, uploads sources, generates artifacts

## Wave 7: NotebookLM Publishing

Wave 7 runs automatically at `comprehensive` depth or when `--waves 1-7` is specified.
Can also be run standalone:

```bash
bm publish notebooklm --config <path>/brand-config.yaml
bm publish notebooklm --config <path>/brand-config.yaml --force
bm publish notebooklm --config <path>/brand-config.yaml --dry-run
bm publish notebooklm --config <path>/brand-config.yaml --no-synthesize
bm publish notebooklm --config <path>/brand-config.yaml --clear-prose-cache
bm publish notebooklm --config <path>/brand-config.yaml --synthesis-model anthropic/claude-sonnet-4
```

**What it does:**
1. Creates a NotebookLM notebook for the brand
2. Synthesizes prose source documents from skill outputs using LLM (OpenRouter)
3. Falls back to mechanical rendering if `OPENROUTER_API_KEY` is not set
4. Uploads all sources (prose + images) with smart curation
5. Waits for all sources to index
6. Generates artifacts: mind-map, slide decks, brand report, audio overview
7. Downloads all artifacts to `deliverables/notebooklm/`

**Prose Synthesis:** Source documents are transformed from raw JSON into narrative prose
written *as* the brand using the voice-and-tone skill output. Requires `OPENROUTER_API_KEY`.
Can be configured in brand-config.yaml:

```yaml
publishing:
  synthesize: true          # default: true (set false to disable)
  synthesis_model: ""       # default: anthropic/claude-3.5-haiku
```

**Requires:** `pip install 'brandmint[publishing]'` (installs notebooklm-py)

## Post-Pipeline Publishing (Wiki)

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
- Prose cache: `<brand-dir>/.brandmint/prose-cache/`
- Pipeline state: `<brand-dir>/.brandmint/state.json`
- Deliverables: `<brand-dir>/deliverables/notebooklm/`
- NotebookLM state: `<brand-dir>/.brandmint/notebooklm-state.json`
